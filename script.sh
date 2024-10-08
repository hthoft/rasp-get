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

# Step 4: Modify /boot/firmware/config.txt
echo "Step 4: Modifying /boot/firmware/config.txt..."
sudo sed -i 's/dtoverlay=vc4-kms-v3d/dtoverlay=vc4-kms-dpi-hyperpixel4:rotate/g' /boot/firmware/config.txt
echo "display_lcd_rotate=3" | sudo tee -a /boot/firmware/config.txt
sudo sed -i '/MatchIsTouchscreen "on"/a Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"' /usr/share/X11/xorg.conf.d/40-libinput.conf


# Step 5: Install Python Dependencies
echo "Step 5: Installing necessary Python libraries..."
pip3 install brother_ql pyusb dotenv pillow psutil fcntl flask flask_socketio requests flask_cors qrcode pywebview --break-system-packages

# Step 6: Setup Printer Environment
echo "Step 6: Setting up Brother QL-700 printer..."
read -p "Please enter your new Printer Serial Number (PRINTER_SN): " printer_sn

# Clone rasp-get repository and create .env file
echo "Step 7: Cloning rasp-get repository and setting up environment variables..."
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

# Step 8: Verify Printer Connection
echo "Step 8: Checking if Brother QL-700 is detected..."
lsusb | grep "04f9:2042" > /dev/null
if [ $? -ne 0 ]; then
    echo "Brother QL-700 printer not found. Please check the connection and try again."
    exit 1
else
    echo "Brother QL-700 printer detected!"
fi

# Step 9: Run a Test Print
echo "Step 9: Running a test print..."
test_image_path="dark-logo-white.png"
if [ ! -f "$test_image_path" ]; then
    echo "Creating a placeholder test image..."
    convert -size 300x300 xc:white -gravity Center -pointsize 24 -annotate +0+0 "Test Print" $test_image_path
fi
BROTHER_QL_PRINTER=usb://0x04f9:0x2042 BROTHER_QL_MODEL=QL-700 brother_ql print -l 62 $test_image_path
echo "Test print initiated. Please check your printer for output."

# Step 10: Setup Kiosk Mode and Auto Start
echo "Step 10: Setting up Kiosk mode and script autostart..."

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

# Step 11: Modify /etc/rc.local for script autostart
echo "Step 11: Modifying /etc/rc.local for script autostart..."
sudo printf "[[ -z \$DISPLAY && \$XDG_VTNR -eq 1 ]] && startx -- -nocursor" | sudo tee .bash_profile

# Step 12: Final Reboot
echo "Step 12: Rebooting to apply all changes..."
sudo reboot
