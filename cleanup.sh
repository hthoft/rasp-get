#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)." 
   exit 1
fi

echo "Starting the uninstallation of HyperPixel services..."

# Step 1: Disable and stop services
echo "Disabling and stopping services: hyperpixel-init and hyperpixel-touch..."
sudo systemctl disable hyperpixel-init &> /dev/null
sudo systemctl disable hyperpixel-touch &> /dev/null
sudo systemctl stop hyperpixel-init &> /dev/null
sudo systemctl stop hyperpixel-touch &> /dev/null

# Step 2: Remove service files
echo "Removing service files from /usr/lib/systemd/system..."
sudo rm /usr/lib/systemd/system/hyperpixel-init.service &> /dev/null
sudo rm /usr/lib/systemd/system/hyperpixel-touch.service &> /dev/null

# Step 3: Remove related binaries
echo "Removing binary files from /usr/bin..."
sudo rm /usr/bin/hyperpixel-init &> /dev/null
sudo rm /usr/bin/hyperpixel-touch &> /dev/null

# Step 4: Remove device tree overlays
echo "Removing device tree overlays..."
sudo rm /boot/overlays/hyperpixel.dtbo &> /dev/null
sudo rm /boot/overlays/hyperpixel-gpio-backlight.dtbo &> /dev/null

# Step 5: Remove configurations from /boot/config.txt
CONFIG=/boot/config.txt
echo "Removing HyperPixel configurations from $CONFIG..."
sudo sed -i '/# HyperPixel LCD Settings/,+17d' $CONFIG

# Step 6: Remove i2c-dev from /etc/modules if added
LOADMOD=/etc/modules
if grep -q "i2c-dev" $LOADMOD; then
    echo "Removing i2c-dev entry from $LOADMOD..."
    sudo sed -i '/i2c-dev/d' $LOADMOD
fi

# Step 7: Reload systemd daemon to apply changes
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Step 8: Remove unused dependencies if installed by the original script
echo "Cleaning up unused dependencies..."
sudo apt-get autoremove --purge python-rpi.gpio python-smbus -y &> /dev/null

# Final Message
echo "Uninstallation completed. All HyperPixel-related services and configurations have been removed."

# Prompt for reboot
read -p "Would you like to reboot the system now? (y/N): " response
if [[ $response =~ ^(yes|y|Y)$ ]]; then
    echo "Rebooting the system..."
    sudo reboot
else
    echo "Reboot later to apply all changes."
fi

exit 0
