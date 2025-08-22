
#!/bin/bash

# Define the name of the virtual environment
ENV_NAME="myenv"

# Remove existing environment if it exists (to fix any issues)
if [ -d "$ENV_NAME" ]; then
    echo "Removing existing virtual environment..."
    rm -rf $ENV_NAME
fi

# Create a new virtual environment
echo "Creating virtual environment $ENV_NAME..."
python3 -m venv $ENV_NAME

# Activate the virtual environment
source $ENV_NAME/bin/activate

echo "Virtual environment $ENV_NAME activated."

# Install/update packages from requirements.txt
pip install -r requirements.txt

# Run the scraper with any passed arguments
python3 scrape.py "$@"

# Deactivate the environment
deactivate