import json
from typing import Dict

def save_state(state: Dict, path: str = "state.json"):
    """
    Save the current state dictionary to a local JSON file.
    """
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def load_last_text(path: str = "last_ocr.txt") -> str:
    """
    Load the previous OCR text from file.
    """
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def update_last_text(text: str, path: str = "last_ocr.txt"):
    """
    Save the new OCR text to file for next comparison.
    """
    with open(path, "w") as f:
        f.write(text)