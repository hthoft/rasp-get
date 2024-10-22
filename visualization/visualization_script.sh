#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)." 
   exit 1
fi

# Ask the user to select the device type
echo "Select the device type:"
echo "1) RPI-5"
echo "2) RPI-4B"
read -p "Enter the number corresponding to your device (1 or 2): " device_choice

# Set the directory and device name based on the user's choice
if [[ "$device_choice" == "1" ]]; then
    DEVICE_NAME="RPI-5"
elif [[ "$device_choice" == "2" ]]; then
    DEVICE_NAME="RPI-4B"
else
    echo "Invalid selection. Please choose either 1 or 2."
    exit 1
fi

echo "You selected $DEVICE_NAME."

# Ask the user for the device serial number
read -p "Enter the device serial number (DEVICE_SN): " DEVICE_SN

# Ask the user for the location name
read -p "Enter the location name (LOCATION_NAME): " LOCATION_NAME

echo "Starting the Raspberry Pi setup..."

# Step 1: Update System and Install Dependencies
echo "Step 1: Updating system and installing dependencies..."
sudo apt-get update && sudo apt-get upgrade -y
sleep 2  # Delay

# Step 2: Fix Broken Dependencies
echo "Step 2: Fixing broken dependencies..."
sudo apt-get --fix-broken install -y
sleep 2  # Delay

# Step 3: Install required packages including PyQt and Python dependencies
echo "Step 3: Installing necessary packages..."
sudo apt-get install --no-install-recommends -y python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer git xserver-xorg x11-xserver-utils xinit openbox chromium-browser libgirepository1.0-dev gir1.2-webkit2-4.0 libgtk-3-dev libwebkit2gtk-4.0-dev qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools python3-pyqt5 python3-gi python3-gi-cairo gir1.2-gtk-3.0 plymouth-themes
sleep 2  # Delay

# Step 4: Disable Splash and Default RPi Features
echo "Step 4: Disabling splash screen and reducing default output for faster boot..."

# Add config.txt settings if not already present
config_file="/boot/firmware/config.txt"
if ! grep -q "disable_splash=1" "$config_file"; then
    echo "disable_splash=1" | sudo tee -a "$config_file"
    echo "Added disable_splash=1 to config.txt"
else
    echo "disable_splash=1 already exists in config.txt"
fi

# Add cmdline.txt settings if not already present
cmdline_file="/boot/firmware/cmdline.txt"
if ! grep -q "logo.nologo" "$cmdline_file"; then
    echo "logo.nologo consoleblank=0 loglevel=1 quiet vt.global_cursor_default=0" | sudo tee -a "$cmdline_file"
    echo "Added logo.nologo and other settings to cmdline.txt"
else
    echo "cmdline settings already exist"
fi
sleep 2  # Delay

# Step 5: Set custom splash screen using Plymouth
echo "Step 5: Setting custom splash screen..."

# Copy the splash image (replace with the path to your splash.png)
splash_image_path="/home/$DEVICE_NAME/rasp-get/splash.png"
if [[ -f "$splash_image_path" ]]; then
    sudo cp "$splash_image_path" /usr/share/plymouth/themes/pix/splash.png
    echo "Copied splash.png to Plymouth theme folder"
else
    echo "splash.png not found in $splash_image_path"
fi

# Set plymouth to use the splash
sudo plymouth-set-default-theme pix
sudo update-initramfs -u

sleep 2  # Delay

# Step 6: Add Xserver fbdev configuration
echo "Step 6: Adding Xserver fbdev configuration..."

# Create the X11 configuration file for fbdev
sudo tee /etc/X11/xorg.conf.d/99-fbdev.conf > /dev/null <<EOT
Section "Device"
    Identifier "FBDEV"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
    BusID "PCI:0:2:0"
EndSection
EOT

echo "fbdev configuration added successfully."
sleep 2  # Delay

# Step 7: Disable Unnecessary System Services
echo "Step 7: Disabling unused services like getty@tty3..."
sudo systemctl disable getty@tty3
sleep 2  # Delay

# Step 8: Install Python Dependencies
echo "Step 8: Installing necessary Python libraries..."
pip3 install requests --break-system-packages
pip3 install Flask --break-system-packages
pip3 install flask-cors --break-system-packages
pip3 install threading --break-system-packages
pip3 install psutil --break-system-packages
pip3 install platform --break-system-packages
pip3 install flask_socketio --break-system-packages
pip3 install python-dotenv --break-system-packages
pip3 install pywebview --break-system-packages
pip3 install PyGObject --break-system-packages

sleep 2  # Delay

# Step 9: Clone rasp-get repository and create .env file
echo "Step 9: Cloning rasp-get repository and setting up environment variables..."
cat <<EOT >> .env
API_KEY=eba2db587a73af3e49c82f07e2205570ad2acee28f15ad37d2d3d0e73dbc5047
CUSTOMER_ID=8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
DEVICE_SN=$DEVICE_SN
DISPLAY_NAME=Maprova
LOCATION_ID=0
LOCATION_NAME=$LOCATION_NAME
CURRENT_VERSION=1.1.0
EOT
sleep 2  # Delay 

mv .env /home/$DEVICE_NAME/

# Step 13: Setup Kiosk Mode and Auto Start
echo "Step 13: Setting up Kiosk mode and script autostart..."

# Add autostart for openbox
autostart_file="/etc/xdg/openbox/autostart"
if ! grep -q "chromium-browser" "$autostart_file"; then
    echo "xset s off\nxset s noblank\nxset -dpms\nsetxkbmap -option terminate:ctrl_alt_bksp\ncd rasp-get/visualization/\npython3 visualization.py &\nsleep 5\nchromium-browser --kiosk http://localhost:5000/visualization &" | sudo tee -a "$autostart_file"
    echo "Added Kiosk mode setup to openbox autostart"
else
    echo "Kiosk mode already set in openbox autostart"
fi
sleep 2  # Delay

# Replace all instances of RPI-5 with RPI-4B in visualization.py if device is RPI-4B
if [[ "$DEVICE_NAME" == "RPI-4B" ]]; then
    echo "Updating visualization.py to replace instances of RPI-5 with RPI-4B..."
    sed -i 's/RPI-5/RPI-4B/g' /home/$DEVICE_NAME/rasp-get/visualization/visualization.py
    echo "Replaced RPI-5 with RPI-4B in visualization.py."
fi

# Step 14: Creating a systemd service for starting X on boot
echo "Step 14: Creating a systemd service to run startx on boot..."

bashrc_file="/home/$DEVICE_NAME/.bashrc"
if ! grep -q "startx -- -nocursor" "$bashrc_file"; then
    echo -e "\n# Start X when logging in on tty1\nif [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then\n    startx -- -nocursor\nfi" | sudo tee -a "$bashrc_file"
    echo "startx added to .bashrc"
else
    echo "startx is already in .bashrc"
fi

# Ensure permissions are correct for .bashrc
chown $DEVICE_NAME:$DEVICE_NAME "$bashrc_file"
chmod 644 "$bashrc_file"

sleep 2  # Delay

# Step 15: Final Reboot
echo "Step 15: Rebooting to apply all changes..."
sleep 2  # Delay
sudo reboot
