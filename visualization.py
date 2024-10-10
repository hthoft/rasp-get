import requests
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import threading
import os
import webview
import psutil
import platform
from datetime import timedelta, datetime
import time
import subprocess
import json
from flask_socketio import SocketIO  
import subprocess
import socket
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key, customer ID, and printer serial number
api_key = os.getenv('API_KEY')
customer_id = os.getenv('CUSTOMER_ID')
printer_sn = os.getenv('VISUALIZATION_SN')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple route to display a white page
@app.route('/')
def index():
    # This inline HTML returns a simple white page
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>White Page</title>
        <style>
          body {
            background-color: white;
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
          }
        </style>
      </head>
      <body>
      </body>
    </html>
    ''')

# Function to run Flask server
def run_flask():
    socketio.run(app, host='127.0.0.1', port=5000)

# Function to run Webview window
def run_webview():
    time.sleep(2)  # Add a small delay to ensure the Flask server is running before opening the Webview
    webview.create_window('White Page', 'http://127.0.0.1:5000', width=800, height=600)
    webview.start()

# Run Flask and Webview in parallel threads
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    run_webview()  # Start the webview window
