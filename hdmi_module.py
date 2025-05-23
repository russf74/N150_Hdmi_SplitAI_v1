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

def preprocess_image(frame):
    # Crop 160 pixels from all four edges
    h, w = frame.shape[:2]
    cropped = frame[160:h-160, 160:w-160]
    # Convert to grayscale for OCR
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    return gray

def save_frame(image, filename):
    cv2.imwrite(filename, image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])