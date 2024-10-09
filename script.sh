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
sudo apt-get install --no-install-recommends -y \
    python3-pip libusb-1.0-0-dev ttf-mscorefonts-installer git \
    xserver-xorg x11-xserver-utils xinit openbox chromium-browser \
    libgirepository1.0-dev gir1.2-webkit2-4.0 libgtk-3-dev \
    libwebkit2gtk-4.0-dev qt5-default python3-pyqt5 
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

# Step 6: Modify /boot/firmware/config.txt and /usr/share/X11/xorg.conf.d/40-libinput.conf
echo "Step 6: Modifying /boot/firmware/config.txt and touchscreen settings..."

# Check and replace the dtoverlay line if necessary
if grep -q "dtoverlay=vc4-kms-dpi-hyperpixel4:rotate" /boot/firmware/config.txt; then
    echo "dtoverlay already set correctly."
else
    sudo sed -i 's/dtoverlay=vc4-kms-v3d/dtoverlay=vc4-kms-dpi-hyperpixel4:rotate/g' /boot/firmware/config.txt
    echo "dtoverlay modified."
fi

# Check if display_lcd_rotate is already set, and add it if not
if grep -q "display_lcd_rotate=3" /boot/firmware/config.txt; then
    echo "display_lcd_rotate is already set."
else
    echo "display_lcd_rotate=3" | sudo tee -a /boot/firmware/config.txt
    echo "display_lcd_rotate added."
fi

# Check and modify touchscreen configuration if necessary
if grep -q 'Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"' /usr/share/X11/xorg.conf.d/40-libinput.conf; then
    echo "TransformationMatrix option is already set."
else
    sudo sed -i '/MatchIsTouchscreen "on"/a Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"' /usr/share/X11/xorg.conf.d/40-libinput.conf
    echo "TransformationMatrix option added."
fi

sleep 2  # Delay


# Step 7: Install Brother QL-710W Driver
echo "Step 7: Installing Brother QL-710W printer driver..."
if [ -f "./ql710wpdrv-2.1.4-0.armhf.deb" ]; then
    sudo dpkg -i ./ql710wpdrv-2.1.4-0.armhf.deb
else
    echo "Error: Brother QL-710W driver package not found. Please ensure 'ql710wpdrv-2.1.4-0.armhf.deb' is in the current directory."
    exit 1
fi
sleep 2  # Delay

# Step 8: Install Python Dependencies
echo "Step 8: Installing necessary Python libraries..."
pip3 install requests Flask flask-cors threading psutil platform Pillow rcode flask-socketio python-dotenv pywebview[qt] --break-system-packages
pip3 install brother_ql --break-system-packages
pip3 install pyusb --break-system-packages
sleep 2  # Delay

# Modify conversions.py to replace antialias with lanczos
echo "Modifying brother_ql conversion.py..."
python3 -c "import brother_ql.conversion; import fileinput; for line in fileinput.input(brother_ql.conversion.__file__, inplace=True): print(line.replace('Image.ANTIALIAS', 'Image.LANCZOS'), end='')"
sleep 2  # Delay

# Step 9: Clone rasp-get repository and create .env file
echo "Step 9: Cloning rasp-get repository and setting up environment variables..."
cat <<EOT >> .env
API_KEY=c552aca5def31c26f81dcd9d0f0ea8f36c0d43497f8701561855b85ffc47d7f1
CUSTOMER_ID=8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
PRINTER_SN=139132
EOT
sleep 2  # Delay

# Step 10: Set up Brother QL-700 Printer Environment Variables
echo "Setting up environment variables for Brother QL-700..."
echo "export BROTHER_QL_PRINTER=usb://0x04f9:0x2042" >> ~/.bashrc
echo "export BROTHER_QL_MODEL=QL-700" >> ~/.bashrc
source ~/.bashrc
sleep 2  # Delay

# Step 11: Verify Printer Connection
echo "Step 11: Checking if Brother QL-700 is detected..."
lsusb | grep "04f9:2042" > /dev/null
if [ $? -ne 0 ]; then
    echo "Brother QL-700 printer not found. Please check the connection and try again."
    exit 1
else
    echo "Brother QL-700 printer detected!"
fi
sleep 2  # Delay

# Step 12: Run a Test Print
echo "Step 12: Running a test print..."
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
sleep 2  # Delay

# Step 13: Setup Kiosk Mode and Auto Start
echo "Step 13: Setting up Kiosk mode and script autostart..."

# Add autostart for openbox
echo "Setting up Openbox autostart..."
sudo printf "xset s off\nxset s noblank\nxset -dpms\nxrandr --output DPI-1 --rotate left\nsetxkbmap -option terminate:ctrl_alt_bksp\ncd rasp-get/\npython3 main.py" | sudo tee /etc/xdg/openbox/autostart
sleep 2  # Delay

# Modify .bashrc to autostart X without a cursor
echo "Adding autostart to .bashrc for non-GUI mode..."
sleep 2  # Delay

# Step 14: Modify /etc/rc.local for script autostart
echo "Step 14: Modifying /etc/rc.local for script autostart..."

# Check if the rc.local file exists, create it if not
if [ ! -f /etc/rc.local ]; then
    sudo tee /etc/rc.local > /dev/null <<EOT
#!/bin/sh -e
# rc.local
# This script is executed at the end of each multiuser runlevel.

exit 0
EOT
    sudo chmod +x /etc/rc.local
fi

# Add the startx command to /etc/rc.local
sudo sed -i '$i [[ -z "$DISPLAY" && "$XDG_VTNR" -eq 1 ]] && startx -- -nocursor\n' /etc/rc.local
sleep 2  # Delay

# Step 15: Final Reboot
echo "Step 15: Rebooting to apply all changes..."
sleep 2  # Delay
sudo reboot
