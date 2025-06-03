import os
import re
import anthropic
from typing import Dict, Any, List, Tuple

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    print("WARNING: ANTHROPIC_API_KEY not found in environment variables.")
    client = None

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

def build_answer_prompt(question_data: Dict[str, Any]) -> str:
    """Build a prompt for the answer evaluation task."""
    exam_type = get_exam_type()
    
    # Reconstruct the question and answers into a prompt
    question_text = question_data.get("question", "")
    options = question_data.get("options", {})
    
    # Format options
    options_text = ""
    for letter, text in sorted(options.items()):
        options_text += f"{letter}: {text}\n"
    
    prompt_text = f"""
You are an expert in {exam_type} certification exams. Analyze this question and answer options, then determine which answers are correct based on {exam_type} best practices and standards. For each answer option, provide a percentage in brackets indicating how correct you believe it is.

Question: {question_text}

Answer Options:
{options_text}

Example output format:
A (100%) [Answer A text]
B (0%) [Answer B text]
C (42%) [Answer C text]
D (87%) [Answer D text]

EVALUATION INSTRUCTIONS:
- If the question asks for a specific number of answers (e.g., "select 2 answers"), you must assign the highest confidence percentages to exactly that number of answers.
- Do not assign the same highest confidence to more answers than requested.
- The highest confidence does not have to be 100%—use your best judgment.
- All other answers must have a lower confidence than the selected ones.
- For example, if asked to select 2, you might use 92% and 87% for the top two, and lower values for the rest.
- Never assign the same top confidence to more answers than requested.
- Take your time and carefully evaluate each question and answer
- For standard single-answer questions, assign higher percentages to better answers, with your best answer receiving the highest percentage
- Only assign 100% when you're absolutely confident an answer is correct
- It's acceptable to have no options at 100% if you're uncertain about all answers
- For multiple-choice questions that specifically request multiple answers (e.g., "Select all that apply", "Choose two"), assign higher percentages to each option you believe is correct, but never more than the requested number
- Be honest about your confidence level - use percentages that truly reflect your certainty
- Use any percentage from 0% to 100% to represent your confidence in each answer's correctness
- When a question asks for a specific number of answers (e.g., "select 2"), you must not assign the same highest confidence to more than that number of answers

Also at the bottom of your answer, present all the answers and their percentages in this format: A:50%, B:20%, C:100%, etc.
"""
    return prompt_text

def evaluate_answers(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate which answers are correct for the given question."""
    # Check if question data is valid
    if "error" in question_data:
        return {"error": question_data["error"]}
    
    if not question_data.get("question") or not question_data.get("options"):
        return {"error": "Invalid question data provided"}
    
    prompt = build_answer_prompt(question_data)
    
    if not ANTHROPIC_API_KEY:
        return {"error": "Anthropic API key is missing"}
    
    try:
        # Call the AI model to evaluate the answers
        message = client.messages.create(
            model="claude-3-opus-20240229",  # Use the more powerful model for answer evaluation
            max_tokens=1000,
            temperature=0.0,  # Keep deterministic
            system="You are a helpful assistant that evaluates exam questions and determines correct answers.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Process the response
        if message and hasattr(message, 'content') and message.content:
            evaluation_text = message.content[0].text
            
            # Parse the evaluated content
            answer_labels, confidences = parse_answer_evaluation(evaluation_text)
            
            return {
                "question": question_data["question"],
                "evaluations": evaluation_text,
                "answer_labels": answer_labels,
                "confidences": confidences
            }
        else:
            return {"error": "Empty response from AI model"}
    
    except Exception as e:
        error_msg = f"Error calling Anthropic API: {e}"
        print(error_msg)
        return {"error": str(e)}

def parse_answer_evaluation(evaluation_text: str) -> Tuple[List[str], List[str]]:
    """Parse the answer evaluation to extract labels and confidence percentages."""
    # Initialize default values
    answer_labels = ["NA"] * 8
    confidence_values = ["0"] * 8
    
    # Extract confidence values using regex
    letter_pattern = r"([A-Z])\s*\((\d+)%\)"
    matches = re.findall(letter_pattern, evaluation_text)
    
    # Map letters to indices (A=0, B=1, etc.)
    letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
    
    for letter, confidence in matches:
        if letter in letter_to_index:
            index = letter_to_index[letter]
            answer_labels[index] = letter
            confidence_values[index] = confidence
    
    # Also check for the summary format at the bottom
    summary_pattern = r"([A-Z]):(\d+)%"
    summary_matches = re.findall(summary_pattern, evaluation_text)
    
    # If we found a summary and didn't find any matches with the first pattern, use the summary
    if summary_matches and not matches:
        for letter, confidence in summary_matches:
            if letter in letter_to_index:
                index = letter_to_index[letter]
                answer_labels[index] = letter
                confidence_values[index] = confidence
    
    # Check for True/False questions
    true_false_question = False
    if "True" in evaluation_text and "False" in evaluation_text:
        true_false_pattern = r"(True|False)\s*\((\d+)%\)"
        tf_matches = re.findall(true_false_pattern, evaluation_text)
        if tf_matches:
            true_false_question = True
    
    # Special handling for True/False questions
    if true_false_question and all(label == "NA" for label in answer_labels[:2]):
        true_pattern = r"True\s*\((\d+)%\)"
        false_pattern = r"False\s*\((\d+)%\)"
        
        true_match = re.search(true_pattern, evaluation_text)
        false_match = re.search(false_pattern, evaluation_text)
        
        if true_match:
            answer_labels[0] = "True"
            confidence_values[0] = true_match.group(1)
        
        if false_match:
            answer_labels[1] = "False"
            confidence_values[1] = false_match.group(1)
    
    return answer_labels, confidence_values

if __name__ == "__main__":
    # Test function
    test_question = {
        "question": "Which of the following is a benefit of information security governance?",
        "options": {
            "A": "Direct involvement of senior management in developing control processes",
            "B": "Reduction of the potential for civil and legal liability",
            "C": "Questioning the trust in vendor relationships",
            "D": "Increasing the risk of decisions based on incomplete management information"
        }
    }
    
    result = evaluate_answers(test_question)
    print("Evaluation result:")
    print(f"Question: {result.get('question')}")
    print("Evaluations:")
    print(result.get('evaluations'))
    print("Processed results:")
    for i, (label, confidence) in enumerate(zip(result.get('answer_labels', []), result.get('confidences', []))):
        if label != "NA":
            print(f"{label}: {confidence}%")