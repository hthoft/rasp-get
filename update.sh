#!/bin/bash

# Kill the main.py process
kill -9 $(pgrep -f main.py)

# Pull the latest changes from the git repository, excluding setup.sh
git fetch --all
git reset --hard origin/main
git clean -f -d

chmod +x script.sh
chmod +x update.sh


# Wait for a couple of seconds
sleep 2

# Reboot the system
sudo reboot
