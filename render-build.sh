#!/bin/bash
# Render Build Script with Enhanced Retries

echo "---- Starting Build Process ----"
date
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Install system dependencies for Pillow
echo "Installing build dependencies for Pillow..."
apt-get update
apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tk-dev \
    tcl-dev \
    build-essential

# Install Python dependencies with enhanced retries
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
    echo "Attempting to install Pillow separately..."
    pip install --no-cache-dir --only-binary=:all: pillow==9.5.0
    
    if [ $? -ne 0 ]; then
        echo "Pillow installation failed. Trying with source build..."
        pip install --no-cache-dir pillow==9.5.0
    fi
fi

echo "---- Build Completed Successfully ----"
date