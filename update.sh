#!/bin/bash

# Define paths
PROJECT_DIR="/home/RPI-5/rasp-get"
PARENT_DIR="/home/RPI-5"
ENV_FILE="$PROJECT_DIR/.env"
ENV_BACKUP="$PARENT_DIR/.env.bak"

# Kill the main.py process
kill -9 $(pgrep -f main.py)

# Move the .env file to the parent directory
if [ -f "$ENV_FILE" ]; then
    echo "Moving the .env file to the parent directory..."
    mv "$ENV_FILE" "$ENV_BACKUP"
fi

# Pull the latest changes from the git repository, excluding setup.sh
cd "$PROJECT_DIR"
git fetch --all
git reset --hard origin/main
git clean -f -d

# Move the .env file back to the project directory
if [ -f "$ENV_BACKUP" ]; then
    echo "Moving the .env file back to the project directory..."
    mv "$ENV_BACKUP" "$ENV_FILE"
fi

# Make the scripts executable
chmod +x script.sh
chmod +x update.sh

# Wait for a couple of seconds
sleep 2

# Reboot the system 
sudo reboot
