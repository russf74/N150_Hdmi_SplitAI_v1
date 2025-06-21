import time
import datetime
import cv2
import os
import shutil
import re
import multiprocessing
import subprocess
import threading
from log_utils import setup_logging, log
from hdmi_module import preprocess_image, save_frame
from ocr_module import run_ocr
from clean_text_module import clean_text
from ai_module import parse_answers, map_confidence_to_colors, build_prompt, ask_gpt
from led_module import update_leds  # Remove duplicate import from here
from state_manager import save_state
from question_extractor import extract_question
from answer_processor import evaluate_answers
from question_comparator import compare_questions

OUTPUT_DIR = "output"
LOG_FILE = os.path.join(OUTPUT_DIR, "exam_processor.log")

exit_flag = False

def clear_output_folder():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    else:
        for filename in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

def start_web_monitor():
    # Start the Flask web monitor as a subprocess
    subprocess.Popen([
        "python3", os.path.join(os.path.dirname(__file__), "web_monitor.py")
    ])

def input_listener():
    global exit_flag
    while True:
        try:
            user_input = input()
            if user_input.strip().lower() in ("q", "exit", "quit"):
                print("Exit command received. Shutting down...")
                exit_flag = True
                break
        except EOFError:
            break

def main():
    global exit_flag
    # Start the web monitor in a separate process (if not already)
    try:
        start_web_monitor()
    except Exception:
        pass
    # Start input listener thread
    listener = threading.Thread(target=input_listener, daemon=True)
    listener.start()

    # Show exam type at startup
    from ai_module import get_exam_type
    exam_type = get_exam_type()
    print(f"\n\033[93mExam type: {exam_type}\033[0m")
    print("(To change, edit the file: exam_type.txt in your project folder)")

    clear_output_folder()
    setup_logging(LOG_FILE)
    log("Exam Processor started.")

    # Immediately set all LEDs to blue (reset state) at startup
    try:
        from led_module import update_leds
        update_leds(["b"] * 8)
    except Exception as e:
        print(f"[WARN] Could not set initial LED reset: {e}")

    AnswerLabels = ["NA"] * 8
    LEDColors = ["b"] * 8
    last_question_text = None

    # Open the HDMI capture device ONCE
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    previous_frame_filename = os.path.join(OUTPUT_DIR, "previous_frame.jpg")
    pause_state_path = os.path.join(OUTPUT_DIR, "pause_state.json")

    while not exit_flag:
        # Check pause state at the start of each loop
        pause = False
        try:
            if os.path.exists(pause_state_path):
                import json
                with open(pause_state_path, "r") as f:
                    pause_data = json.load(f)
                if pause_data.get("paused"):
                    pause = True
        except Exception as e:
            print(f"[WARN] Could not read pause state: {e}")
            # If error, default to not paused
            pause = False

        if pause:
            print("[PAUSED] Backend processing is paused. Waiting...")
            time.sleep(1)
            continue

        # Make loop iteration visible in terminal
        print("\n\033[96m*** New loop iteration ***\033[0m")
        log("New loop iteration")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_filename = os.path.join(OUTPUT_DIR, f"frame_{timestamp}.jpg")
        preproc_filename = frame_filename.replace(".jpg", "_proc.jpg")
        ocr_filename = os.path.join(OUTPUT_DIR, f"ocr_output_{timestamp}.txt")
        state_filename = os.path.join(OUTPUT_DIR, "state.json")
        ai_prompt_filename = os.path.join(OUTPUT_DIR, f"ai_prompt_{timestamp}.txt")
        ai_response_filename = os.path.join(OUTPUT_DIR, f"ai_response_{timestamp}.txt")
        question_extract_filename = os.path.join(OUTPUT_DIR, f"question_extract_{timestamp}.txt")
        answer_eval_filename = os.path.join(OUTPUT_DIR, f"answer_eval_{timestamp}.txt")

        # 1. Capture and preprocess HDMI frame
        try:
            # Add more frame discards to clear any buffered frames
            for _ in range(10):  # Increased from 3 to 10
                cap.read()
                
            # Set these properties to ensure we're not getting cached frames
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Force a small delay to make sure we get a fresh frame
            time.sleep(0.2)
            
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARN] Failed to capture HDMI frame.")
                log("Failed to capture HDMI frame!")
                time.sleep(2)  # Reduced from 5 to 2 seconds to retry faster
                continue

            cv2.imwrite(frame_filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            print(f"Frame saved: {frame_filename}")

            # Add a simple frame difference check
            if os.path.exists(previous_frame_filename):
                prev_frame = cv2.imread(previous_frame_filename)
                if prev_frame is not None:
                    # Calculate the difference between current and previous frame
                    diff = cv2.absdiff(frame, prev_frame)
                    non_zero = cv2.countNonZero(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY))
                    
                    # If frames are very similar, there might not be a new question
                    if non_zero < 10000:  # Threshold for similarity
                        print("[INFO] Screen hasn't changed significantly, checking again...")
                        time.sleep(1)  # Shorter wait time for unchanged screen
                        continue
    
            # Save this as the previous frame for next comparison
            cv2.imwrite(previous_frame_filename, frame)
            
            image = preprocess_image(frame)
            save_frame(image, preproc_filename)
            print(f"Preprocessed frame saved: {preproc_filename}")

        except Exception as e:
            log(f"HDMI capture or preprocessing error: {e}")
            print("[ERROR] HDMI capture or preprocessing error, see log.")
            time.sleep(5)
            continue

        # 2. OCR
        try:
            ocr_text = run_ocr(preproc_filename)
            # print(f"[DEBUG] OCR output:\n{ocr_text}\n{'-'*40}")  # <-- Removed terminal OCR output
            with open(ocr_filename, "w") as f:
                f.write(ocr_text)
            print(f"Raw OCR text saved: {ocr_filename}")
        except Exception as e:
            log(f"OCR error: {e}")
            print("[ERROR] OCR error, see log.")
            time.sleep(5)
            continue

        # 3. AI Processing
        try:
            # Step 1: Extract the question and answers
            question_data = extract_question(ocr_text)
            
            # Save the extracted question for debugging
            with open(question_extract_filename, "w") as f:
                f.write(str(question_data))
            print(f"Extracted question saved: {question_extract_filename}")
            
            # Check if extraction was successful
            if "error" in question_data:
                print(f"[ERROR] Question extraction failed: {question_data['error']}")
                AnswerLabels = ["NA"] * 8
                LEDColors = ["b"] * 8
                continue
    
            # NEW STEP: Compare with previous question
            similarity, should_process = compare_questions(question_data)
            print(f"Question similarity: {similarity:.2f}% - {'Processing' if should_process else 'Skipping'} evaluation")
    
            # If significant change detected, set all LEDs to white to indicate processing
            if should_process:
                print("New question detected! Setting LEDs to white while processing...")
                processing_leds = ["w"] * 8  # All white LEDs
                update_leds(processing_leds)
                # --- NEW: Immediately update state.json to reflect all-white LEDs ---
                processing_state = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "question": "",
                    "answer_labels": ["NA"] * 8,
                    "confidences": ["0"] * 8,
                    "labels": ["NA"] * 8,
                    "led_colors": ["w"] * 8,
                    "ocr_text": ocr_text,
                    "ocr_stable": 0,
                    "change_percent": 0,
                    "extracted_question_response": "",
                    "evaluations": ""
                }
                save_state(processing_state, path="state.json")
                save_state(processing_state, path=state_filename)
                print("State saved with all-white LEDs for processing.")
                # --- END NEW BLOCK ---
                
            # Skip evaluation if question hasn't changed significantly
            if not should_process:
                print("Question unchanged (>80% similar). Skipping evaluation and LED update.")
                continue
                
            # Step 2: Evaluate the answers (only if question has changed significantly)
            evaluation_result = evaluate_answers(question_data)
            
            # Save the evaluation result for debugging
            with open(answer_eval_filename, "w") as f:
                f.write(str(evaluation_result))
            print(f"Answer evaluation saved: {answer_eval_filename}")
            
            # Check if evaluation was successful
            if "error" in evaluation_result:
                print(f"[ERROR] Answer evaluation failed: {evaluation_result['error']}")
                AnswerLabels = ["NA"] * 8
                LEDColors = ["b"] * 8
                continue
                
            # Process the results
            AnswerLabels = evaluation_result.get('answer_labels', ["NA"] * 8)
            confidences = evaluation_result.get('confidences', ["0"] * 8)
            LEDColors = map_confidence_to_colors(confidences, AnswerLabels)
            
            print(f"Parsed labels: {AnswerLabels}")
            print(f"Parsed confidences: {confidences}")
            print(f"LED colors: {LEDColors}")
            print("AI processed OCR text and updated answer labels/LEDs.")
            
        except Exception as e:
            log(f"AI processing error: {e}")
            print(f"[ERROR] AI processing error: {e}")
            AnswerLabels = ["NA"] * 8
            LEDColors = ["b"] * 8

        # 4. Save state
        state = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question_data.get("question", "") if 'question_data' in locals() and 'question' in question_data else "",
            "answer_labels": evaluation_result.get('answer_labels', ["NA"] * 8) if 'evaluation_result' in locals() else ["NA"] * 8,
            "confidences": evaluation_result.get('confidences', ["0"] * 8) if 'evaluation_result' in locals() else ["0"] * 8,
            "labels": AnswerLabels,
            "led_colors": LEDColors,
            "ocr_text": ocr_text,
            "ocr_stable": 0,
            "change_percent": 0,
            "extracted_question_response": None,
            "evaluations": evaluation_result.get('evaluations', '') if 'evaluation_result' in locals() else ''
        }

        # BLANK STATE if all LEDs are white
        if state["led_colors"] == ["w"] * 8:
            state["question"] = ""
            state["answer_labels"] = ["NA"] * 8
            state["confidences"] = ["0"] * 8
            state["labels"] = ["NA"] * 8
            state["ocr_text"] = ""
            state["extracted_question_response"] = ""
            state["evaluations"] = ""
        # Save the full raw OpenAI response if available
        try:
            with open(question_extract_filename, "r") as f:
                state["extracted_question_response"] = f.read()
        except Exception:
            state["extracted_question_response"] = ""
        save_state(state, path="state.json")
        save_state(state, path=state_filename)
        print(f"State saved: {state_filename}")

        # 5. Update LEDs
        try:
            update_leds(LEDColors[::-1])
        except Exception as e:
            log(f"LED update error: {e}")
            print("[ERROR] LED update error, see log.")

        print("-" * 40)
        print("Pausing for 1 second before next iteration...")
        time.sleep(1)
    cap.release()
    # Clean up resources here (e.g., cap.release())
    try:
        from led_module import update_leds
        update_leds(["k"] * 8)  # Set all LEDs to black on exit
        print("All LEDs set to black.")
    except Exception as e:
        print(f"[WARN] Could not set LEDs to black on exit: {e}")

if __name__ == "__main__":
    main()