# HDMI View v4

HDMI capture system for monitoring and evaluating multiple-choice questions.

## Features

- HDMI video capture and processing
- OCR-based question and answer extraction
- AI-powered answer evaluation using Anthropic's Claude model
- LED status indicator integration
- Web-based monitoring UI
- Automated startup and graceful shutdown

## Requirements

- Python 3.12+
- Anthropic API key (for Claude integration)
- HDMI capture hardware
- LED hardware (optional)

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   ```
   export ANTHROPIC_API_KEY=your_key_here
   ```
   Or create a `.env` file with these values.

4. Run the application:
   ```
   python main.py
   ```

## Web Monitor

The web monitoring interface starts automatically with the main application. It can be accessed at `http://localhost:8000`.

## Keyboard Commands

- `q` or `quit`: Exit the application gracefully
- (Ctrl+C also works for clean exit)

## Configuration

- Edit `exam_type.txt` to set the type of exam being processed
- Adjust confidence thresholds in `ai_module.py`

## License

All rights reserved.
