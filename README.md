
# Maprova Devices

Setting up devices for the Maprova system

## Hyperpixel4 + RPI Zero 2W
In order to use the Hyperpixel4 together with the RPI Zero 2W, we must ensure that both are connected in terms of GPIO pins on the headers. 

The RPI must face towards the Hyperpixel4, thus you can only see the bottom of the RPI Zero 2W.

Initially install **Raspian OS Lite (64 bit)** on a SD card, and boot the RPI. Using either SSH or a monitor/keyboard, get the Hyperpixel4 drivers ready.

First install git:

```
sudo apt update
sudo apt upgrade -y
sudo apt-get install git -y
```

Git clone the brances from Pimoroni:
```
git clone https://github.com/pimoroni/hyperpixel4 -b pi3

```

Go to the install.sh file:
```
cd hyperpixel4
```

Edit the install.sh file, and add "firmware" to the line:
```
CONFIG="/boot/firmware/config.txt"
```

Save the install.sh file, and make it sudo executable, and run it:

```
sudo chmod +x install.sh
sudo ./install.sh
```

Press **y / n** in the prompts and select PI3 - Rectangle. 

When installation is complete, do not accept a reboot. Instead do the following:

```
hyperpixel4-rotate inverted
```

Now reboot the RPI

### Rotating the Hyperpixel4 touchscreen

Open a terminal and navigate to the configuration directory:

```
cd /usr/share/X11/xorg.conf.d/
```
Edit the touchscreen configuration file:
```
sudo nano 40-libinput.conf
```
Find the touchscreen section:
```
Section "InputClass"
    Identifier "libinput touchscreen catchall"
    MatchIsTouchscreen "on"
    MatchDevicePath "/dev/input/event*"
    Driver "libinput"
```
Add the following line to the touchscreen section:
```
Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"
```
Save and exit:

Press Ctrl + X, then Y, and Enter to save.
Reboot your Raspberry Pi:

```
sudo reboot
```



## Hyperpixel4 + Raspberry Pi 5 ##
For using the Hyperpixel4 with the Raspberry Pi 5, only a few adjustments are necessary. No driver installation is required, just a configuration change in the boot firmware.

Add the following line to the /boot/firmware/config.txt file:
```
dtoverlay=hyperpixel4
```

To rotate the screen, apply the following transformation matrix.

Open the touchscreen configuration file:

```
cd /usr/share/X11/xorg.conf.d/
sudo nano 40-libinput.conf
```
In the InputClass section, add the line:

```
Option "TransformationMatrix" "0 -1 1 1 0 0 0 0 1"
```
Save and exit the file by pressing Ctrl + X, then Y, and Enter.

Reboot your Raspberry Pi:
```
sudo reboot
```
