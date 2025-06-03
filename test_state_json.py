import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "state.json")

def print_state():
    print("\n===== state.json contents =====")
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
        for k, v in data.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(f"Error reading state.json: {e}")

if __name__ == "__main__":
    print_state()
