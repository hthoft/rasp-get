#!/bin/bash

# Kill the main.py process

# Check if main.py is running and kill it
if pgrep -f main.py > /dev/null; then
    sudo kill -9 $(pgrep -f main.py)
fi

# Check if visualization.py is running and kill it
if pgrep -f visualization.py > /dev/null; then
    sudo kill -9 $(pgrep -f visualization.py)
fi


# Pull the latest changes from the git repository, excluding setup.sh
git fetch --all
git reset --hard origin/main
git clean -f -d

chmod +x script.sh
chmod +x update.sh


# Wait for a couple of seconds
sleep 2

sudo reboot
