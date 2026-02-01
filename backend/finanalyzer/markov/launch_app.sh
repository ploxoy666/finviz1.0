#!/bin/bash
# Stock Market Prediction App Launcher
# This script launches the Python app in Terminal

# Get the directory where this script is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the app directory
cd "$APP_DIR"

# Clear the screen for a clean start
clear

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Setting up Python environment for first time..."
    echo "This will only happen once..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    echo "Setup complete!"
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Run the Python app in interactive mode
python3 main.py

# Keep terminal open after completion
echo ""
echo "Press any key to close..."
read -n 1
