import time
import datetime
import cv2
import os
import shutil
import re
from log_utils import setup_logging, log
from hdmi_module import preprocess_image, save_frame
from ocr_module import run_ocr
from clean_text_module import clean_text
from ai_module import send_to_openai, parse_answers, map_confidence_to_colors, build_prompt
from led_module import update_leds
from state_manager import save_state

OUTPUT_DIR = "output"
LOG_FILE = os.path.join(OUTPUT_DIR, "exam_processor.log")

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

def main():
    clear_output_folder()
    setup_logging(LOG_FILE)
    log("Exam Processor started.")

    AnswerLabels = ["NA"] * 8
    LEDColors = ["b"] * 8
    last_question_text = None

    # Open the HDMI capture device ONCE
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while True:
        log("New loop iteration.")

        # Timestamp for this loop
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_filename = os.path.join(OUTPUT_DIR, f"frame_{timestamp}.jpg")
        preproc_filename = frame_filename.replace(".jpg", "_proc.jpg")
        ocr_filename = os.path.join(OUTPUT_DIR, f"ocr_output_{timestamp}.txt")
        state_filename = os.path.join(OUTPUT_DIR, "state.json")
        ai_prompt_filename = os.path.join(OUTPUT_DIR, f"ai_prompt_{timestamp}.txt")
        ai_response_filename = os.path.join(OUTPUT_DIR, f"ai_response_{timestamp}.txt")

        # 1. Capture and preprocess HDMI frame
        try:
            for _ in range(3):
                cap.read()
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARN] Failed to capture HDMI frame.")
                log("Failed to capture HDMI frame!")
                time.sleep(5)
                continue

            cv2.imwrite(frame_filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            print(f"[INFO] Frame saved: {frame_filename}")

            image = preprocess_image(frame)
            save_frame(image, preproc_filename)
            print(f"[INFO] Preprocessed frame saved: {preproc_filename}")

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
            print(f"[INFO] Raw OCR text saved: {ocr_filename}")
        except Exception as e:
            log(f"OCR error: {e}")
            print("[ERROR] OCR error, see log.")
            time.sleep(5)
            continue

        # 3. Send to AI (only if OCR output is decent)
        if len(ocr_text.strip()) < 30:
            print("[INFO] OCR output too short, skipping AI call.")
            AnswerLabels = ["NA"] * 8
            LEDColors = ["b"] * 8
        else:
            try:
                prompt = build_prompt(ocr_text)
                with open(ai_prompt_filename, "w") as f:
                    f.write(prompt)
                print(f"[INFO] AI prompt saved: {ai_prompt_filename}")

                response = send_to_openai(ocr_text)
                with open(ai_response_filename, "w") as f:
                    f.write(response)
                print(f"[INFO] AI response saved: {ai_response_filename}")

                # --- New logic: Extract and compare question text ---
                question_match = re.search(r'Question:\s*(.*)', response)
                question_text = question_match.group(1).strip() if question_match else ""

                if last_question_text is not None and question_text and question_text != last_question_text:
                    LEDColors = ["b"] * 8
                    update_leds(LEDColors[::-1])
                    print("[INFO] New question detected, LEDs reset to blue.")
                    # Optional: short pause to ensure reset is visible
                    time.sleep(0.2)

                last_question_text = question_text

                # Debug: Show AI response and parsed results
                try:
                    print(f"[DEBUG] AI response content:\n{response}\n{'-'*40}")
                    AnswerLabels, confidences = parse_answers(response)
                    print(f"[DEBUG] Parsed labels: {AnswerLabels}")
                    print(f"[DEBUG] Parsed confidences: {confidences}")
                    LEDColors = map_confidence_to_colors(confidences, AnswerLabels)
                    print(f"[DEBUG] LED colors: {LEDColors}")
                    print("[INFO] AI processed OCR text and updated answer labels/LEDs.")
                except Exception as e:
                    log(f"AI parsing error: {e}")
                    print(f"[ERROR] AI parsing error: {e}")
                    AnswerLabels = ["NA"] * 8
                    LEDColors = ["b"] * 8

            except Exception as e:
                log(f"AI module error: {e}")
                print("[ERROR] AI module error, see log.")
                AnswerLabels = ["NA"] * 8
                LEDColors = ["b"] * 8

        # 4. Save state
        state = {
            "labels": AnswerLabels,
            "led_colors": LEDColors,
            "ocr_text": ocr_text,
        }
        save_state(state, path=state_filename)
        print(f"[INFO] State saved: {state_filename}")

        # 5. Update LEDs
        try:
            update_leds(LEDColors[::-1])
            print("[INFO] LEDs updated.")
        except Exception as e:
            log(f"LED update error: {e}")
            print("[ERROR] LED update error, see log.")

        print("-" * 40)
        time.sleep(0.2)  # Keep your fast loop

    cap.release()

if __name__ == "__main__":
    main()