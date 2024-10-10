#!/bin/bash

# Kill the main.py process
kill -9 $(pgrep -f main.py)

# Pull the latest changes from the git repository, excluding setup.sh
git pull --rebase --exclude=setup.sh

# Wait for a couple of seconds
sleep 2

# Reboot the system
sudo reboot
