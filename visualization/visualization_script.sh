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
sudo apt-get install --no-install-recommends -y python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer git xserver-xorg x11-xserver-utils xinit openbox chromium-browser libgirepository1.0-dev gir1.2-webkit2-4.0 libgtk-3-dev libwebkit2gtk-4.0-dev qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools python3-pyqt5 python3-gi python3-gi-cairo gir1.2-gtk-3.0 fbi
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

# Step 5: Set custom splash screen
echo "Step 5: Setting custom splash screen..."

# Copy the splash image (replace with the path to your splash.png)
splash_image_path="/home/RPI-5/rasp-get/splash.png"
if [[ -f "$splash_image_path" ]]; then
    sudo cp "$splash_image_path" /usr/share/plymouth/themes/pix/splash.png
    echo "Copied splash.png to Plymouth theme folder"
else
    echo "splash.png not found in $splash_image_path"
fi

# Enable splash screen during boot using fbi
sudo tee /etc/systemd/system/splashscreen.service > /dev/null <<EOT
[Unit]
Description=Splash screen during boot
DefaultDependencies=no
After=local-fs.target

[Service]
ExecStart=/usr/bin/fbi -T 1 -d /dev/fb0 --noverbose -a /usr/share/plymouth/themes/pix/splash.png
StandardInput=tty
StandardOutput=tty

[Install]
WantedBy=sysinit.target
EOT

# Enable the service
sudo systemctl enable splashscreen
sleep 2  # Delay

# Step 6: Disable Unnecessary System Services
echo "Step 6: Disabling unused services like getty@tty3..."
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
DEVICE_SN=98844435
DISPLAY_NAME=Maprova
LOCATION_ID=0
LOCATION_NAME=Tegnestuen_2
EOT
sleep 2  # Delay 

# Step 13: Setup Kiosk Mode and Auto Start
echo "Step 13: Setting up Kiosk mode and script autostart..."

# Add autostart for openbox
autostart_file="/etc/xdg/openbox/autostart"
if ! grep -q "chromium-browser" "$autostart_file"; then
    echo "xset s off\nxset s noblank\nxset -dpms\nsetxkbmap -option terminate:ctrl_alt_bksp\ncd rasp-get/visualization/\npython3 visualization.py & chromium-browser --kiosk http://localhost:5000/visualization" | sudo tee -a "$autostart_file"
    echo "Added Kiosk mode setup to openbox autostart"
else
    echo "Kiosk mode already set in openbox autostart"
fi
sleep 2  # Delay

# Step 14: Creating a systemd service for starting X on boot
echo "Step 14: Creating a systemd service to run startx on boot..."

bashrc_file="/home/RPI-5/.bashrc"
if ! grep -q "startx -- -nocursor" "$bashrc_file"; then
    echo -e "\n# Start X when logging in on tty1\nif [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then\n    startx -- -nocursor\nfi" | sudo tee -a "$bashrc_file"
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
