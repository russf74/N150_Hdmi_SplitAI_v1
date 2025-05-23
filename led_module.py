from typing import List
import serial
import time

def update_leds(colors: List[str], port: str = "/dev/ttyACM0", baudrate: int = 115200):
    """
    Send 8 color codes to the ESP32 LED controller via serial USB.
    """
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        color_str = ''.join(colors) + '\n'  # <-- Add newline here!
        print(f"Sending to ESP32: {repr(color_str)}")
        ser.write(color_str.encode('utf-8'))
        time.sleep(0.1)
        ser.close()
    except Exception as e:
        print(f"LED update failed: {e}")