#!/bin/bash
# Render Build Script with Advanced Network Resilience

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
    tk-dev \
    tcl-dev \
    build-essential \
    curl

# Function to install with retries and mirror fallback
install_with_resilience() {
    local package=$1
    local mirrors=(
        "https://pypi.org/simple"
        "https://pypi.tuna.tsinghua.edu.cn/simple"
        "https://mirrors.aliyun.com/pypi/simple"
        "https://pypi.mirrors.ustc.edu.cn/simple"
    )
    
    for mirror in "${mirrors[@]}"; do
        for i in {1,2,3}; do
            echo "Attempt $i with mirror $mirror: Installing $package"
            pip install --no-cache-dir --retries 3 --timeout 60 --index-url "$mirror" --trusted-host "${mirror#https://}" "$package"
            
            if [ $? -eq 0 ]; then
                echo "$package installed successfully!"
                return 0
            else
                echo "Installation failed. Retrying in 5 seconds..."
                sleep 5
            fi
        done
    done
    
    echo "ERROR: Failed to install $package after multiple attempts"
    return 1
}

# Install core dependencies with enhanced resilience
install_with_resilience pandas==2.0.3
install_with_resilience pillow==10.3.0

# Install remaining dependencies with mirror rotation
for i in {1,2,3}; do
    echo "Attempt $i: Installing requirements.txt"
    pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt
    
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
    echo "ERROR: Failed to install dependencies after multiple attempts"
    exit 1
fi

echo "---- Build Completed Successfully ----"
date