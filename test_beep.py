import sys
import os
import time
from led_module import play_beep

if __name__ == "__main__":
    print("Testing play_beep() from led_module.py...")
    for i in range(3):
        print(f"Beep {i+1}...")
        play_beep()
        time.sleep(1)
    print("Done. If you did not hear any sound, check your speaker and the sounds/mouseclick.wav file.")
    print("You can also try: aplay sounds/mouseclick.wav")
