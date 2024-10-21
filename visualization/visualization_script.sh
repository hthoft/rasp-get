#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)." 
   exit 1
fi

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
sudo apt-get install --no-install-recommends -y python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer git xserver-xorg x11-xserver-utils xinit openbox chromium-browser libgirepository1.0-dev gir1.2-webkit2-4.0 libgtk-3-dev libwebkit2gtk-4.0-dev qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools python3-pyqt5 python3-gi python3-gi-cairo gir1.2-gtk-3.0
sleep 2  # Delay

# Step 4: Disable Splash and Default RPi Features
echo "Step 4: Disabling splash screen and reducing default output for faster boot..."
sudo tee -a /boot/firmware/config.txt <<< "disable_splash=1"
sudo tee -a /boot/firmware/cmdline.txt <<< "logo.nologo consoleblank=0 loglevel=1 quiet vt.global_cursor_default=0"
sleep 2  # Delay

# Step 5: Disable Unnecessary System Services
echo "Step 5: Disabling unused services like getty@tty3..."
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
DEVICE_SN=53935837
EOT
sleep 2  # Delay 


# Step 13: Setup Kiosk Mode and Auto Start
echo "Step 13: Setting up Kiosk mode and script autostart..."

# Add autostart for openbox
echo "Setting up Openbox autostart..."
sudo printf "xset s off\nxset s noblank\nxset -dpms\nsetxkbmap -option terminate:ctrl_alt_bksp\ncd rasp-get/\npython3 visualization.py & chromium-browser --kiosk http://localhost/visualization" | sudo tee /etc/xdg/openbox/autostart
sleep 2  # Delay

# Modify .bashrc to autostart X without a cursor
echo "Adding autostart to .bashrc for non-GUI mode..."
sleep 2  # Delay

# Step 14: Creating a systemd service for starting X on boot
echo "Step 14: Creating a systemd service to run startx on boot..."
# Append the startx command to /home/RPI-5/.bashrc if it's not already there
bashrc_file="/home/RPI-5/.bashrc"
if ! grep -q "startx -- -nocursor" "$bashrc_file"; then
    echo -e "\n# Start X when logging in on tty1\nif [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then\n    startx -- -nocursor\nfi" | tee -a "$bashrc_file"
    echo "startx added to .bashrc"
else
    echo "startx is already in .bashrc"
fi

# Ensure permissions are correct for .bashrc
chown RPI-5:RPI-5 "$bashrc_file"
chmod 644 "$bashrc_file"

sleep 2  # Delay



# Step 15: Final Reboot
echo "Step 15: Rebooting to apply all changes..."
sleep 2  # Delay
sudo reboot
