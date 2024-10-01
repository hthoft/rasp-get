#!/bin/bash


# Install Brother QL printer driver from a .deb file
echo "Installing the Brother QL printer driver..."
sudo dpkg -i --force-all ql710wpdrv-2.1.4-0.armhf.deb
sudo apt --fix-broken install -y


#!/bin/bash

# Update the package list
echo "Updating package list..."
sudo apt update

# Install required packages
echo "Installing necessary packages..."
sudo apt install -y python3-pip libusb-1.0-0-dev python3-pil git

# Install the brother_ql Python library and dependencies
echo "Installing brother_ql library..."
pip3 install brother_ql pyusb qrcode[pil] pillow

# Check if the printer is connected
echo "Checking for connected Brother QL printer..."
lsusb | grep '04f9:2043'

if [ $? -eq 0 ]; then
    echo "Brother QL-710W printer detected."
else
    echo "Brother QL-710W printer not detected. Please check your connection."
    exit 1
fi

# Define a test QR code image generation function
generate_test_qr() {
    echo "Generating test QR code..."
    python3 - <<EOF
import qrcode
from PIL import Image

# Generate a test QR code
qr_data = "Test QR Code for Brother QL-710W"
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=1,
)

qr.add_data(qr_data)
qr.make(fit=True)

# Create an image from the QR code
img = qr.make_image(fill='black', back_color='white')

# Save the test image
img.save("test_qr.png")

print("Test QR code saved as 'test_qr.png'.")
EOF
}

# Generate a test QR code
generate_test_qr

# Test print the QR code using the Brother QL printer
echo "Printing test QR code..."
sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2043 BROTHER_QL_MODEL=QL-710W brother_ql print -l 62 test_qr.png

# Confirm the test print
if [ $? -eq 0 ]; then
    echo "Test print successful. Check the printer for the output."
else
    echo "Test print failed. Please check the printer connection and settings."
    exit 1
fi

# Cleanup
echo "Cleaning up..."
rm test_qr.png

echo "Setup complete. Your Brother QL-710W printer is ready to use!"
