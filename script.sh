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
sudo apt-get install -y python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer git xserver-xorg x11-xserver-utils xinit openbox chromium-browser

# Step 2: Disable Splash and Default RPi Features
echo "Step 2: Disabling splash screen and reducing default output for faster boot..."
sudo tee -a /boot/firmware/config.txt <<< "disable_splash=1"
sudo tee -a /boot/firmware/cmdline.txt <<< "logo.nologo consoleblank=0 loglevel=1 quiet vt.global_cursor_default=0"

# Step 3: Disable Unnecessary System Services
echo "Step 3: Disabling unused services like getty@tty3..."
sudo systemctl disable getty@tty3

# Step 4: Setup Hyperpixel4 Screen
echo "Step 4: Setting up Hyperpixel4 drivers and touchscreen configuration..."
git clone https://github.com/pimoroni/hyperpixel4 -b pi3
cd hyperpixel4
sed -i 's/CONFIG="\/boot\/config.txt"/CONFIG="\/boot\/firmware\/config.txt"/g' install.sh
sudo chmod +x install.sh
./install.sh
hyperpixel4-rotate inverted

# Step 5: Adjust Hyperpixel4 Touchscreen Configuration
echo "Step 5: Adjusting touchscreen rotation..."
sudo sed -i '/MatchIsTouchscreen "on"/a Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"' /usr/share/X11/xorg.conf.d/40-libinput.conf

# Step 6: Install Python Dependencies
echo "Step 6: Installing necessary Python libraries..."
pip3 install brother_ql pyusb dotenv pillow psutil fcntl flask flask_socketio requests flask_cors qrcode pywebview --break-system-packages


# Step 7: Setup Printer Environment
echo "Step 7: Setting up Brother QL-700 printer..."
read -p "Please enter your new Printer Serial Number (PRINTER_SN): " printer_sn

# Clone rasp-get repository and create .env file
echo "Step 8: Cloning rasp-get repository and setting up environment variables..."
cat <<EOT >> .env
API_KEY=c552aca5def31c26f81dcd9d0f0ea8f36c0d43497f8701561855b85ffc47d7f1
CUSTOMER_ID=8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
PRINTER_SN=$printer_sn
EOT

# Set up Brother QL-700 Printer Environment Variables
echo "Setting up environment variables for Brother QL-700..."
echo "export BROTHER_QL_PRINTER=usb://0x04f9:0x2042" >> ~/.bashrc
echo "export BROTHER_QL_MODEL=QL-700" >> ~/.bashrc
source ~/.bashrc

# Step 9: Verify Printer Connection
echo "Step 9: Checking if Brother QL-700 is detected..."
lsusb | grep "04f9:2042" > /dev/null
if [ $? -ne 0 ]; then
    echo "Brother QL-700 printer not found. Please check the connection and try again."
    exit 1
else
    echo "Brother QL-700 printer detected!"
fi

# Step 10: Run a Test Print
echo "Step 10: Running a test print..."
test_image_path="dark-logo-white.png"
if [ ! -f "$test_image_path" ]; then
    echo "Creating a placeholder test image..."
    convert -size 300x300 xc:white -gravity Center -pointsize 24 -annotate +0+0 "Test Print" $test_image_path
fi
BROTHER_QL_PRINTER=usb://0x04f9:0x2042 BROTHER_QL_MODEL=QL-700 brother_ql print -l 62 $test_image_path
echo "Test print initiated. Please check your printer for output."

# Step 11: Setup Kiosk Mode and Auto Start
echo "Step 11: Setting up Kiosk mode and script autostart..."

# Add autostart for openbox
echo "Setting up Openbox autostart..."
mkdir -p /etc/xdg/openbox
echo "python3 ~/rasp-get/main.py &" >> /etc/xdg/openbox/autostart

# Modify .bashrc to autostart X without a cursor
echo "Adding autostart to .bashrc for non-GUI mode..."
cat <<EOT >> ~/.bashrc
if [ -z "\$DISPLAY" ] && [ "\$XDG_VTNR" -eq 1 ]; then
    startx -- -nocursor
fi
EOT

# Step 12: Modify /etc/rc.local for script autostart
echo "Step 12: Modifying /etc/rc.local for script autostart..."
sudo sed -i '/exit 0/i [[ -z "\$DISPLAY" && "\$XDG_VTNR" -eq 1 ]] && startx -- -nocursor' /etc/rc.local

# Step 13: Final Reboot
echo "Step 13: Rebooting to apply all changes..."
sudo reboot
