#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Setup complete! Run ./run.sh to start the app."
