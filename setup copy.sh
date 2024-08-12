#!/bin/bash
# Maprova - Martin Cornelius 2024

if [ "$(id -u)" != "0" ]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

###############################
# MAIN SETUP                  #
###############################

# Variables
rpiUsername="RPI-4B"

# Ask for RPi Serial Number
read -p "Enter RPi Serial Number: " rpiSerialNumber

read -p "Enter device hash: " deviceHash

echo "Setting up RPI with the following parameters:"
echo "Hash device: $deviceHash"
echo "RPI Serial Number: $rpiSerialNumber"

echo "Starting setup process"
sudo mv /home/RPI-4B/rpiserver.service /etc/systemd/system/
sudo mkdir RPIServer
sudo mv /home/RPI-4B/RPIServer.js /home/RPI-4B/RPIServer/RPIServer.js

sudo apt-get update
sudo apt-get upgrade -y

sudo raspi-config nonint do_wifi_country DK

# Turn off default rpi
echo "disable_splash=1" | sudo tee -a /boot/firmware/config.txt

echo " logo.nologo consoleblank=0 loglevel=1 quiet vt.global_cursor_default=0" | sudo tee -a /boot/firmware/cmdline.txt

sudo systemctl disable getty@tty3

# X11 setup
sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox -y

# Chromium browser
sudo apt-get install --no-install-recommends chromium-browser -y

# Setup kiosk mode
sudo printf "xset s off\nxset s noblank\nxset -dpms\nsetxkbmap -option terminate:ctrl_alt_bksp\nchromium-browser --disable-infobars --kiosk 'https://portal.maprova.dk/Visualisering/autoview.php?deviceTag=$rpiSerialNumber&deviceHash=$deviceHash'" | sudo tee /etc/xdg/openbox/autostart
sudo printf "[[ -z \$DISPLAY && \$XDG_VTNR -eq 1 ]] && startx -- -nocursor" | sudo tee .bash_profile

# Install and setup node and service
sudo apt-get install nodejs -y
sudo systemctl daemon-reload
sudo systemctl enable rpiserver.service
sudo systemctl start rpiserver.service

# Setting timezone
echo "Configuring timezone..."
sudo timedatectl set-timezone Europe/Copenhagen
echo "Timezone configured to Denmark's timezone successfully."
sudo raspi-config
