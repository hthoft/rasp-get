#!/bin/bash

# Update and upgrade the system
echo "Updating the system..."
sudo apt update && sudo apt upgrade -y

# Install Python and Pip
echo "Installing Python and pip..."
sudo apt install python3 python3-pip python3-tk -y

# Install required Python libraries
echo "Installing required Python libraries..."
pip3 install Pillow qrcode brother_ql

# Install Brother QL printer driver from a .deb file
echo "Installing the Brother QL printer driver..."
sudo dpkg -i ql710wpdrv-2.1.4-0.armhf.deb
sudo apt --fix-broken install -y

# Install additional required packages
echo "Installing CUPS and dependencies..."
sudo apt install libcups2 libcupsimage2 -y

# Set up Brother QL printer with CUPS
echo "Setting up the printer..."
sudo lpadmin -p PrinterA2 -E -v usb://Brother_QL-710W -m everywhere
sudo cupsenable PrinterA2
sudo cupsaccept PrinterA2

echo "Setup complete! You can now run your print.py script."
