#!/bin/bash

# Script to set up Brother QL-700 without CUPS on a Raspberry Pi

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)." 
   exit 1
fi

# Update package list and install necessary system dependencies
echo "Updating system and installing dependencies..."
apt update && apt install -y python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer

# Install Python libraries required for Brother QL
echo "Installing Python dependencies (brother_ql, pyusb)..."
pip3 install brother_ql pyusb dotenv pillow psutil fcntl

# Verify if the printer is connected
echo "Checking if Brother QL-700 is detected..."
lsusb | grep "04f9:2042" > /dev/null
if [ $? -ne 0 ]; then
    echo "Brother QL-700 printer not found. Please check the connection and try again."
    exit 1
else
    echo "Brother QL-700 printer detected!"
fi

# Export necessary environment variables for Brother QL-700
echo "Setting up environment variables for Brother QL-700..."
echo "export BROTHER_QL_PRINTER=usb://0x04f9:0x2042" >> ~/.bashrc
echo "export BROTHER_QL_MODEL=QL-700" >> ~/.bashrc

# Source the updated .bashrc to apply changes
source ~/.bashrc

# Test print using a sample image (replace with your own test image if necessary)
echo "Running a test print..."
test_image_path="dark-logo-white.png"

# Check if test image exists, and if not, create a placeholder test image
if [ ! -f "$test_image_path" ]; then
    echo "Creating a placeholder test image..."
    convert -size 300x300 xc:white -gravity Center -pointsize 24 -annotate +0+0 "Test Print" $test_image_path
fi

# Run the test print command
BROTHER_QL_PRINTER=usb://0x04f9:0x2042 BROTHER_QL_MODEL=QL-700 brother_ql print -l 62 $test_image_path

echo "Test print initiated. Please check your printer for output."

echo "Installation and setup completed successfully!"
