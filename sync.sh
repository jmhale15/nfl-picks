#!/bin/bash

# Define the name of the virtual environment
ENV_NAME="myenv"

# Check if virtual environment exists
if [ ! -d "$ENV_NAME" ]; then
    echo "❌ Virtual environment $ENV_NAME not found!"
    echo "Please run ./setup.sh first to create the environment."
    exit 1
fi

# Activate the virtual environment
source $ENV_NAME/bin/activate

echo "Virtual environment $ENV_NAME activated."

# Run the sync to Google Sheets script
echo "🏈 Syncing picks to Google Sheets..."
python3 sync-to-sheets.py

# Deactivate the environment
deactivate