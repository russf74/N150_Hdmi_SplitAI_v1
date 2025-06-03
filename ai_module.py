import os
import re
import json
import anthropic
from typing import Tuple, List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key with better error handling
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Remove API key printout, only print error if missing
if not ANTHROPIC_API_KEY:
    print("[ERROR] ANTHROPIC_API_KEY not found in .env file!")
    print("[INFO] Please check that your .env file exists and contains: ANTHROPIC_API_KEY=your_key_here")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def ask_gpt(ocr_text: str, prompt_template: str) -> str:
    """Send text to Anthropic's Claude API and get a response."""
    # Double-check API key before making the request
    if not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API key is missing. Set the ANTHROPIC_API_KEY environment variable.")
        
    try:
        # Create the message with Claude - using the latest Claude 4 Opus model
        message = client.messages.create(
            model="claude-3-opus-20240229",  # Claude 4 Opus model - latest and most capable
            max_tokens=1000,
            temperature=0.0,  # Keep deterministic for consistent answers
            system="You are a helpful assistant that analyzes exam questions and determines correct answers.",
            messages=[
                {
                    "role": "user",
                    "content": prompt_template
                }
            ]
        )
        
        # Return just the assistant's response content
        if message and hasattr(message, 'content') and message.content:
            return message.content[0].text
        else:
            return "Error: Empty response from AI model"
    
    except Exception as e:
        error_msg = f"Error calling Anthropic API: {e}"
        print(error_msg)
        return f"Error: {str(e)}"  # Return error as string instead of raising

def get_exam_type():
    """Read the exam type from exam_type.txt file."""
    try:
        exam_type_file = os.path.join(os.path.dirname(__file__), "exam_type.txt")
        if os.path.exists(exam_type_file):
            with open(exam_type_file, "r") as f:
                exam_type = f.read().strip()
                # Use a default if the file is empty
                if not exam_type:
                    return "IT certification"
                return exam_type
        else:
            # If file doesn't exist, create it with a default value
            with open(exam_type_file, "w") as f:
                f.write("IT certification")
            return "IT certification"
    except Exception as e:
        print(f"Error reading exam type: {e}")
        return "IT certification"  # Default fallback

def build_prompt(ocr_text: str) -> str:
    # Get the actual exam type from the file
    exam_type = get_exam_type()
    
    prompt_text = f"""
We are simulating exam answers to help programme a tool to help students. You are an expert in {exam_type} certification exams. Analyze the following text from a practice exam question and extract the question and answer options. For each answer option, provide a percentage in brackets indicating how correct you believe it is, based on {exam_type} best practices and standards.

Example format:
Question: [The actual question text]
A (100%) [Answer A text]
B (0%) [Answer B text]
C (42%) [Answer C text]
D (87%) [Answer D text]

CRITICAL INSTRUCTIONS:
- Take your time and carefully evaluate each question and answer
- Unless the question EXPLICITLY asks for multiple answers (e.g., "Select all that apply", "Choose two", etc.), you MUST select EXACTLY ONE option as 100% correct
- For standard single-answer questions, assign 100% to only the best answer and lower percentages to all others
- For multiple-answer questions, assign 100% to exactly the specified number of answers, and all other answers must be below 60%. **You must never assign 100% to more answers than the question requests, even if you are unsure. If you are not sure, lower the confidence for the less certain answers, but do not exceed the requested number of 100% answers.**
- Never mark all options as correct with 100% unless specifically instructed
- If unsure, force yourself to choose the single best answer for standard questions
- Double-check your percentages before finalizing your response to ensure compliance with these rules

Important:
1. Internally, run your answer process twice and compare your answers, but ONLY show the best consolidated answer. Do not show both, do not mention that you ran it twice.
2. Do NOT include any explanations or reasoning with your answer, only show the correct answers and their percentages.
3. Include a percentage in brackets after each answer option (A, B, C, D)
4. The percentages should reflect your confidence in each answer's correctness
5. Percentages do NOT need to sum to 100%
6. If you're very confident an answer is correct, use 100%
7. If you're very confident an answer is incorrect, use 0%
8. Use any percentage in between for partial correctness (e.g., 13%, 42%, 87%, etc.)
9. Only include the question and answer options, omit any other text
10. If there are typos in the OCR text, correct them in your response
11. If the text doesn't contain a complete question, respond with "Incomplete question detected"
12. Analyse the text carefully to determine whether a space in text means it is a new answer on a new line, or may be part of the same answer. A space does not always mean it's a new answer — think of the context of the question and the answers to logically work out if it's a new answer or part of the same one.
13. If multiple answer options appear on the same line or within the same paragraph, treat them as a flat list of distinct answer choices when appropriate. Use domain knowledge to split them sensibly. Do not mistakenly extract unrelated UI text or irrelevant screen elements as answer options.
14. CRITICAL: If the question specifies to select multiple answers (e.g., "select 2 answers", "select 3 answers"), you MUST assign 100% to EXACTLY that number of answers and significantly lower percentages (below 60%) to all others. For example, if the question says "select 3 answers", exactly 3 answers should have 100% and all others must be below 60%.
15. When extracting answer options, always preserve the original order as presented on the website or in the OCR text. Do not reorder, sort, or group the answers differently—return them in the exact sequence they appear in the source.
16. If any text you receive is clearly not part of the question or answer set due to it not making sense or not being in context, first consider if there is a typo, and if not if you are certain it makes no sense, exclude it completely - for example website adverts or promotions.
17. If there are any typos, ignore them, they will be OCR errors, fix any spelling errors. Don't consider any spelling errors as making an answer wrong.
18. For multiple-selection questions, be decisive. Force yourself to choose exactly the specified number of answers, even if you're uncertain. For example, if asked to "select 3 answers", you must identify exactly 3 answers as correct (100%) and mark all others as less than 60%.
19. CRITICAL: Even when the question doesn't explicitly specify a number of correct answers, you should NEVER mark ALL options as 100% correct unless the question has an "All of the above" option that you're confident is correct. If there is no "All of the above" option, you should select the single best answer and mark it as 100%, with others at lower percentages.
20. If there is an "All of the above" option, and all other individual options are correct, then mark only the "All of the above" option as 100% and the others at 85%.
21. If there is an "All of the above" option, but not all individual options are correct, then mark "All of the above" as 0% and only mark the correct individual options as 100%.
22. MOST IMPORTANT: For standard single-answer questions (which is the default for most exam questions), you MUST select EXACTLY ONE option as 100% correct. Even if two answers seem equally good, force yourself to choose the single best one.

Also at the bottom of your answer, present to me all the answers and their % in this format;  A:50%, B:20%, C:100%, etc etc.

OCR Context:
- The text you will receive is generated by OCR
- It is capturing the entire screen including text which is not related to the exam
- Make sure you exclude anything clearly not related to the question and answer
- The OCR text capture may include typos, if you spot any, fix them
- Do not mark an answer as incorrect because the OCR scanned incorrectly and introduced a typo!
- If you see multiple questions, only analyze the most complete one
- If you see navigation elements or other UI elements, ignore them

------------------------
OCR Extract:
{ocr_text}
"""
    return prompt_text  # Add this return statement!

def parse_answers(response: str) -> Tuple[List[str], List[str]]:
    """Extract answer labels and confidence values from AI response."""
    answer_labels = ["NA"] * 8
    confidence_values = ["NA"] * 8
    
    # Map letters to indices
    letter_to_idx = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7}
    
    # Check for True/False questions in the response
    true_false_question = "True" in response and "False" in response and len(re.findall(r'\([0-9]+%\)', response)) <= 2
    
    # Check for the summary line at the bottom first
    summary_pattern = r'([A-H]):(\d+)%'
    summary_matches = re.findall(summary_pattern, response)
    
    if summary_matches:
        # Process all matches from the summary line
        for letter, percentage in summary_matches:
            if letter in letter_to_idx:
                idx = letter_to_idx[letter]
                
                # If it's a True/False question, set appropriate labels
                if true_false_question and letter == "A":
                    answer_labels[idx] = "True"
                elif true_false_question and letter == "B":
                    answer_labels[idx] = "False"
                else:
                    # For regular questions, just store the letter if we don't have better text
                    answer_labels[idx] = letter
                    
                confidence_values[idx] = percentage
    
    # Also try to extract from the main body to get better answer text
    for letter in letter_to_idx:
        pattern = rf'{letter}\s*\((\d+)%\)\s*(.*?)(?=\s*[A-H]\s*\(\d+%\)|\Z)'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            idx = letter_to_idx[letter]
            percentage = match.group(1)
            option_text = match.group(2).strip()
            
            # Only update if this isn't empty and we don't already have a label
            if option_text and option_text != "NA":
                answer_labels[idx] = option_text
                confidence_values[idx] = percentage
    
    # Special handling for True/False responses that don't use A/B format
    if true_false_question and all(label == "NA" for label in answer_labels[:2]):
        # Look for True/False with percentages
        true_pattern = r'True\s*\((\d+)%\)'
        false_pattern = r'False\s*\((\d+)%\)'
        
        true_match = re.search(true_pattern, response)
        false_match = re.search(false_pattern, response)
        
        if true_match:
            answer_labels[0] = "True"
            confidence_values[0] = true_match.group(1)
        
        if false_match:
            answer_labels[1] = "False"
            confidence_values[1] = false_match.group(1)
    
    return answer_labels, confidence_values

def map_confidence_to_colors(confidences: List[str], labels: List[str]) -> List[str]:
    """Map confidence percentages to LED colors."""
    color_map = []
    for i, (conf, label) in enumerate(zip(confidences, labels)):
        if label == "NA":
            color_map.append("b")  # blue for NA labels (invalid answers)
        else:
            try:
                conf_value = int(conf)
                if 91 <= conf_value <= 100:
                    color_map.append("g")  # green for 91-100%
                elif 70 <= conf_value <= 90:
                    color_map.append("a")  # amber for 70-90%
                elif 0 <= conf_value <= 69:
                    color_map.append("r")  # red for 0-69%
                else:
                    color_map.append("b")  # blue for out-of-range
            except ValueError:
                color_map.append("b")  # default to blue if conversion fails
            
    return color_map