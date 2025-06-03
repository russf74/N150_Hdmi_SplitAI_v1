import os
import re
import difflib
from typing import Dict, Any, Tuple

# Store the most recently processed question
previous_question_data = None

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate the similarity percentage between two text strings."""
    if not text1 or not text2:
        return 0.0
    
    # Use SequenceMatcher to get similarity ratio
    matcher = difflib.SequenceMatcher(None, text1, text2)
    similarity = matcher.ratio() * 100
    return similarity

def compare_questions(new_question_data: Dict[str, Any]) -> Tuple[float, bool]:
    """
    Compare new question data with previous question data.
    Returns: (similarity_percentage, should_process_further)
    """
    global previous_question_data
    
    # Initialize result
    similarity = 0.0
    should_process = True
    
    # If we have a previous question for comparison
    if previous_question_data is not None and "question" in previous_question_data:
        # Extract question texts
        new_question = new_question_data.get("question", "")
        prev_question = previous_question_data.get("question", "")
        
        # Calculate question similarity
        question_similarity = calculate_similarity(new_question, prev_question)
        
        # Get options for comparison
        new_options = new_question_data.get("options", {})
        prev_options = previous_question_data.get("options", {})
        
        # Calculate options similarity
        options_similarity = 0.0
        if new_options and prev_options:
            # Combine all options into strings for comparison
            new_options_text = " ".join([f"{k}: {v}" for k, v in new_options.items()])
            prev_options_text = " ".join([f"{k}: {v}" for k, v in prev_options.items()])
            options_similarity = calculate_similarity(new_options_text, prev_options_text)
        
        # Calculate overall similarity (weighted average)
        similarity = (question_similarity * 0.7) + (options_similarity * 0.3)
        
        # Determine if we should process further based on similarity
        should_process = similarity < 80.0  # Process if less than 80% similar (meaning > 20% change)
    
    # Store current question data for next comparison
    previous_question_data = new_question_data.copy()
    
    return similarity, should_process