import pytesseract
import cv2
import os
from difflib import SequenceMatcher

def run_ocr(image_path: str) -> str:
    """Run OCR with PSM 11 and return only the output (no terminal print)."""
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        return ""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return ""

    config = '--oem 1 --psm 11'
    text = pytesseract.image_to_string(img, config=config)
    return text

def clean_text(text: str) -> str:
    """Clean OCR text: remove noise, keep valid short words/acronyms."""
    import re

    # Load whitelists if available
    def load_whitelist(filename):
        try:
            with open(filename, "r") as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception:
            return set()

    acronym_whitelist = load_whitelist("acronym_whitelist.txt")
    short_words_whitelist = load_whitelist("short_words_whitelist.txt")

    text = text.lower()
    text = re.sub(r'[^a-z0-9\.\,\s]', '', text)
    lines = text.splitlines()
    seen = set()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Remove lines of 1 or 2 chars unless whitelisted
        if len(line) <= 2 and line not in acronym_whitelist and line not in short_words_whitelist:
            continue
        # Remove short words not in whitelist
        words = line.split()
        filtered_words = []
        for word in words:
            if len(word) <= 3 and word not in acronym_whitelist and word not in short_words_whitelist:
                continue
            filtered_words.append(word)
        filtered_line = ' '.join(filtered_words)
        if filtered_line and filtered_line not in seen:
            cleaned_lines.append(filtered_line)
            seen.add(filtered_line)
    text = ' '.join(cleaned_lines)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_change(new_text: str, last_text: str) -> float:
    """Calculate percent change between two OCR results using fuzzy matching."""
    if not last_text:
        return 100.0
    matcher = SequenceMatcher(None, new_text, last_text)
    similarity = matcher.ratio()
    return 100.0 - (similarity * 100.0)

def is_stable(change_percent: float) -> bool:
    """Return True if OCR change is within the stability threshold."""
    return change_percent <= 30.0