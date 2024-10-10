#!/bin/bash

# Kill the main.py process
kill -9 $(pgrep -f main.py)

# Temporarily stash the .env file to avoid overwriting
if [ -f .env ]; then
    echo "Stashing the .env file..."
    mv .env .env.bak
fi

# Pull the latest changes from the git repository, excluding setup.sh
git fetch --all
git reset --hard origin/main
git clean -f -d

# Restore the .env file after pulling the latest changes
if [ -f .env.bak ]; then
    echo "Restoring the .env file..."
    mv .env.bak .env
fi

# Make the scripts executable
chmod +x script.sh
chmod +x update.sh

# Wait for a couple of seconds
sleep 2

# Reboot the system
sudo reboot
