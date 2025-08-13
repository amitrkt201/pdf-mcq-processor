#!/bin/bash
# Render Build Script - Optimized for Stability

echo "---- Starting Build Process ----"
date
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Install system dependencies
echo "Installing build dependencies..."
apt-get update
apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    build-essential

# Upgrade pip and setuptools first
pip install --no-cache-dir --upgrade pip setuptools wheel

# Install requirements with retries
for i in {1,2,3}; do
    echo "Attempt $i: Installing requirements"
    pip install --no-cache-dir -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "Requirements installed successfully!"
        break
    else
        echo "Installation failed. Retrying in 10 seconds..."
        sleep 10
    fi
done

# Final check
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies after 3 attempts"
    exit 1
fi

echo "---- Build Completed Successfully ----"
date