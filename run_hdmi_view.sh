#!/bin/bash
# Script to run HDMI_View_v4 application

# Change to the application directory
cd /home/russ/Documents/HDMI_View_v4

# Check if .venv exists and activate it
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables if needed
# Uncomment and modify as needed
# export ANTHROPIC_API_KEY="your_key_here"
# export OPENAI_API_KEY="your_key_here"

# Run the application
python main.py

# Keep terminal open after execution
echo
echo "Press Enter to close this window..."
read
