import subprocess
import os
import time

def check_audio_devices():
    """List all audio devices on the system"""
    print("=== Checking audio devices ===")
    
    # Check ALSA devices
    print("\nALSA audio devices:")
    subprocess.run(["aplay", "-l"])
    
    # Check if amixer can see the device
    print("\nChecking audio mixer settings:")
    try:
        result = subprocess.run(
            ["amixer", "-c", "1", "sget", "Master"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"Error getting mixer settings: {e}")

def test_simple_sound():
    """Test a simple sound using different methods"""
    print("\n=== Testing simple beep with different methods ===")
    
    # Method 1: Use ALSA with card 0
    print("\nMethod 1: Testing with card 0, device 0")
    try:
        subprocess.run(["aplay", "-D", "plughw:0,0", "/usr/share/sounds/alsa/Front_Center.wav"])
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Use ALSA with card 1
    print("\nMethod 2: Testing with card 1, device 0")
    try:
        subprocess.run(["aplay", "-D", "plughw:1,0", "/usr/share/sounds/alsa/Front_Center.wav"])
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 3: Default audio device
    print("\nMethod 3: Testing with default audio device")
    try:
        subprocess.run(["aplay", "/usr/share/sounds/alsa/Front_Center.wav"])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_audio_devices()
    test_simple_sound()
    print("\nDid you hear any sounds? (y/n)")
