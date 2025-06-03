import os
import openai
import re
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def test_openai_api():
    """Test if the OpenAI API is working."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Make a simple test request
        response = client.chat.completions.create(
            model="gpt-4",  # You can change this to gpt-3.5-turbo if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working? Please respond with 'Yes, the OpenAI API is working correctly.'"}
            ],
            max_tokens=50
        )
        
        # Check if we got a valid response
        if hasattr(response, 'choices') and len(response.choices) > 0:
            print("SUCCESS: OpenAI API is working!")
            print(f"Response: {response.choices[0].message.content}")
            return True
        else:
            print("ERROR: Got a response but it's not in the expected format")
            print(f"Response: {response}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to call OpenAI API: {e}")
        return False

def test_question_extraction():
    """Test if the OpenAI API can properly extract a question from OCR text."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Sample OCR text with a question
        test_ocr = """
        20:15 Exam Navigation Button
        
        Which of the following is a benefit of information security governance?
        A Direct involvement of senior management in developing control processes
        B Reduction of the potential for civil and legal liability
        C Questioning the trust in vendor relationships
        D Increasing the risk of decisions based on incomplete management information
        
        Next Question Button    Previous Question Button
        """
        
        # Build a prompt for question extraction
        prompt = f"""
        We are extracting exam questions. Analyze the following text from a practice exam question and extract ONLY the question and answer options. Do NOT evaluate which answers are correct - just extract and format the content.

        Example format:
        Question: [The actual question text]
        A: [Answer A text]
        B: [Answer B text]
        C: [Answer C text]
        D: [Answer D text]

        Important:
        1. Do NOT include any evaluations, percentages, or indicators of correctness
        2. Just extract and format the question and answer options
        3. Format as shown above with the letter and colon (e.g., "A: [text]")
        4. If there are typos in the OCR text, correct them in your response
        5. If the text doesn't contain a complete question, respond with "Incomplete question detected"
        6. Only include the question and answer options, omit any other text

        OCR Extract:
        {test_ocr}
        """
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4",  # You can change this to gpt-3.5-turbo if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts exam questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        
        # Check if we got a valid response
        if hasattr(response, 'choices') and len(response.choices) > 0:
            extracted_text = response.choices[0].message.content
            print("\nSUCCESS: Question extraction test completed!")
            print("Extracted content:")
            print(f"{extracted_text}")
            
            # Parse the response to verify format
            result = parse_extracted_content(extracted_text)
            print("\nParsed structure:")
            print(f"Question: {result.get('question')}")
            print("Options:")
            for letter, text in result.get('options', {}).items():
                print(f"{letter}: {text}")
                
            # Count answers to ensure all were extracted
            if len(result.get('options', {})) >= 4:
                print("\nAll answer options successfully extracted!")
                return True
            else:
                print(f"\nWARNING: Only {len(result.get('options', {}))} answer options extracted, expected at least 4")
                return False
        else:
            print("ERROR: Got a response but it's not in the expected format")
            print(f"Response: {response}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to call OpenAI API for question extraction: {e}")
        return False

def parse_extracted_content(extracted_text: str) -> Dict[str, Any]:
    """Parse the extracted text into a structured format."""
    result = {
        "question": "",
        "options": {}
    }
    
    # Check for incomplete question
    if "Incomplete question detected" in extracted_text:
        return {"error": "Incomplete question detected"}
    
    # Extract the question
    question_match = re.search(r"Question: (.+?)(?=\nA:|$)", extracted_text, re.DOTALL)
    if question_match:
        result["question"] = question_match.group(1).strip()
    
    # Extract answer options
    option_pattern = r"([A-Z]): (.+?)(?=\n[A-Z]:|$)"
    options = re.findall(option_pattern, extracted_text, re.DOTALL)
    
    for letter, text in options:
        result["options"][letter] = text.strip()
    
    return result

if __name__ == "__main__":
    print("Testing OpenAI API connection...")
    basic_test = test_openai_api()
    
    if basic_test:
        print("\n\nTesting question extraction capability...")
        test_question_extraction()