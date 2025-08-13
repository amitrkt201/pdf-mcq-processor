#!/bin/bash
# Render Build Script with Network Resilience

echo "---- Starting Build Process ----"
date
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Install system dependencies for Pillow
echo "Installing build dependencies..."
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

# Function to install with retries and network resilience
install_with_retry() {
    local package=$1
    for i in {1,2,3,4,5}; do
        echo "Attempt $i: Installing $package"
        pip install --no-cache-dir --only-binary=:all: "$package"
        if [ $? -eq 0 ]; then
            echo "$package installed successfully!"
            return 0
        else
            echo "Installation failed. Retrying in 10 seconds..."
            sleep 10
        fi
    done
    echo "ERROR: Failed to install $package after 5 attempts"
    return 1
}

# Install core dependencies with network resilience
install_with_retry pandas==2.0.3
install_with_retry pillow==10.3.0

# Install remaining dependencies
pip install --no-cache-dir -r requirements.txt

echo "---- Build Completed Successfully ----"
date