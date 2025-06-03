from typing import List
import serial
import time
import os
import subprocess

# Serial port configuration
ESP32_PORT = "/dev/ttyUSB0"  # Change this to match your ESP32 port
ESP32_BAUD = 115200

previous_colors = None  # Track previous LED colors

def play_beep():
    """Play a mouse click sound using the USB speaker (default device)."""
    try:
        # Path to your custom WAV file
        click_file = os.path.join(os.path.dirname(__file__), "sounds", "mouseclick.wav")
        
        # Create the sounds directory if it doesn't exist
        sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir)
        
        # Download the mouse click sound if it doesn't exist
        if not os.path.exists(click_file):
            try:
                import urllib.request
                click_url = "http://www.kalmanovitz.co.il/courses/English/construction/Assets/Mousclik.wav"
                print(f"Downloading mouse click sound from {click_url}")
                urllib.request.urlretrieve(click_url, click_file)
                print(f"Mouse click sound downloaded to {click_file}")
            except Exception as e:
                print(f"Could not download mouse click sound: {e}")
                # Fall back to creating a beep
                try:
                    subprocess.run(
                        ["sox", "-n", click_file, "synth", "0.15", "sine", "880", "vol", "1.0"],
                        stderr=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL
                    )
                    print("Created fallback beep sound instead")
                except:
                    print("Could not create fallback sound with sox")
        
        # Do NOT set volume automatically; let user control system volume
        # Play the sound (default device)
        if os.path.exists(click_file):
            subprocess.run(
                ["aplay", "-q", click_file],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
        else:
            print("\a")  # Console bell as fallback
    except Exception as e:
        print(f"Sound error: {e}")
        print("\a")  # Console bell as fallback

def update_leds(colors: List[str], port: str = "/dev/ttyACM0", baudrate: int = 115200):
    """
    Send 8 color codes to the ESP32 LED controller via serial USB.
    Play beep any time LEDs are set to a real answer (not all blue or all white).
    """
    global previous_colors
    
    all_blue = all(color == "b" for color in colors)
    all_white = all(color == "w" for color in colors)
    
    # Succinct info print
    print(f"Current colours : {''.join(colors)}")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        color_str = ''.join(colors) + '\n'
        ser.write(color_str.encode('utf-8'))
        if not all_blue and not all_white:
            play_beep()
            previous_colors = colors.copy()
        else:
            pass
        response = ser.readline().decode().strip()
        if response:
            print(f"ESP32: {response}")
        ser.close()
    except Exception as e:
        print(f"LED update failed: {e}")
        try:
            if os.name == 'posix':
                os.system(f"echo '{color_str}' > {port}")
                print(f"[INFO] Used fallback method to send: '{color_str.strip()}'")
                if not all_blue and not all_white:
                    play_beep()
                    previous_colors = colors.copy()
        except Exception as e2:
            print(f"Fallback method failed: {e2}")

def test_speaker():
    """Test the USB speaker with different sounds (default device)."""
    print("Testing speaker with different sounds...")
    
    try:
        # Create the sounds directory if it doesn't exist
        sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir)
        
        # Test 1: System beep
        print("Test 1: System beep")
        print("\a")  # Console bell
        time.sleep(1)
        
        # Test 2: Create and play a sine wave beep
        print("Test 2: Sine wave beep")
        beep_file = os.path.join(sounds_dir, "test_beep.wav")
        try:
            subprocess.run(
                ["sox", "-n", beep_file, "synth", "0.5", "sine", "880", "vol", "1.0"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
            
            # Set volume to 100% for testing (default card)
            subprocess.run(
                ["amixer", "sset", "Master", "100%"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
            
            # Play the sound (default device)
            subprocess.run(
                ["aplay", beep_file],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Test 2 failed: {e}")
        
        time.sleep(1)
        
        # Test 3: Create and play a different tone
        print("Test 3: Higher frequency tone")
        high_beep_file = os.path.join(sounds_dir, "test_high_beep.wav")
        try:
            subprocess.run(
                ["sox", "-n", high_beep_file, "synth", "0.5", "sine", "1760", "vol", "1.0"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
            
            # Play the sound (default device)
            subprocess.run(
                ["aplay", high_beep_file],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Test 3 failed: {e}")
            
        time.sleep(1)
        
        # Test 4: Try to use speaker-test utility (default device)
        print("Test 4: Using speaker-test utility")
        try:
            subprocess.run(
                ["speaker-test", "-c", "2", "-t", "sine", "-f", "440", "-l", "1"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Test 4 failed: {e}")
            
        # Verify the mouseclick sound file exists and try playing it
        print("\nChecking if mouseclick sound exists...")
        click_file = os.path.join(os.path.dirname(__file__), "sounds", "mouseclick.wav")
        if os.path.exists(click_file):
            print(f"Mouseclick sound file exists: {click_file}")
            file_size = os.path.getsize(click_file)
            print(f"File size: {file_size} bytes")
            
            # Try playing it with increased volume (default card)
            print("Playing mouseclick sound at maximum volume...")
            try:
                subprocess.run(
                    ["amixer", "sset", "Master", "100%"],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
                
                subprocess.run(
                    ["aplay", click_file],
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"Failed to play mouseclick: {e}")
        else:
            print("Mouseclick sound file doesn't exist!")
            
        print("Speaker tests completed.")
        
    except Exception as e:
        print(f"Speaker test error: {e}")

# Add this to the bottom of your led_module.py file for testing
if __name__ == "__main__":
    print("Setting all LEDs to blue (reset state)...")
    update_leds(["b"] * 8)
    print("Testing beep function...")
    play_beep()
    print("Test completed")
    test_speaker()