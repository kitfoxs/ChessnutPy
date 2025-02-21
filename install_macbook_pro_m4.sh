#!/bin/bash

# Install Python 3.8
echo "Installing Python 3.8..."
brew install python@3.8

# Create a virtual environment
echo "Creating a virtual environment..."
python3.8 -m venv .venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source .venv/bin/activate

# Install required dependencies
echo "Installing required dependencies..."
pip install -r requirements.txt

# Set macbook_pro_m4_compat flag to true in the configuration file
echo "Setting macbook_pro_m4_compat flag to true in the configuration file..."
CONFIG_FILE="~/.config/chessnutair.config"
if grep -q "macbook_pro_m4_compat" "$CONFIG_FILE"; then
    sed -i '' 's/macbook_pro_m4_compat = false/macbook_pro_m4_compat = true/' "$CONFIG_FILE"
else
    echo "macbook_pro_m4_compat = true" >> "$CONFIG_FILE"
fi

echo "Installation and configuration complete. You can now run the program using 'python main.py'."
