import cv2
import numpy as np

def capture_frame(device_index: int = 0) -> np.ndarray:
    cap = cv2.VideoCapture(device_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame from HDMI device.")
    return frame

def preprocess_image(image):
    """
    Preprocess the captured HDMI frame for better OCR results:
    - Convert to grayscale
    - Crop top and bottom margins but keep full width
    - Adaptive thresholding for better text recognition
    """
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Define crop parameters - remove pixels from top and bottom only
    top_margin = int(height * 0.05)     # Remove 5% from top
    bottom_margin = int(height * 0.05)  # Remove 5% from bottom
    
    # Crop the image (keep full width, trim top and bottom)
    cropped = image[top_margin:height-bottom_margin, 0:width]
    
    # Convert to grayscale
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to improve text visibility
    # (especially helpful for dark backgrounds with light text)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return thresh

def save_frame(image, filename):
    cv2.imwrite(filename, image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])