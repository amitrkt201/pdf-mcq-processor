#!/bin/bash
# Render Build Script with Retries

echo "---- Starting Build Process ----"
date

# Install dependencies with retries
for i in {1..5}; do
    echo "Attempt $i: Installing Python dependencies..."
    pip install --no-cache-dir -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "Dependencies installed successfully!"
        break
    else
        echo "Installation failed. Retrying in 30 seconds..."
        sleep 30
    fi
done

# Check if installation succeeded
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies after 5 attempts"
    exit 1
fi

echo "---- Build Completed Successfully ----"
date