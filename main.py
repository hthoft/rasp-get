import hashlib
import requests
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import os
import webview

app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

# Function to fetch all projects from Maprova API
def fetch_all_projects():
    api_key = '7fd67c060bff8fad72e3b82206d3e49020727b214e1b5bf7cf9df3ceb9a28f44'
    customer_id = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    url = f"https://portal.maprova.dk/api/getAllProjects.php?apiKey={api_key}&customerID={customer_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching projects: {e}")
        return {}

# Flask route to serve project data
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = fetch_all_projects()
    return jsonify(projects)

# Function to start Flask in a separate thread
def start_flask():
    app.run(debug=True, host='0.0.0.0', use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Specify the path to your index.html file
    html_file = os.path.join(current_dir, 'index.html')

    # Create a webview window to open the local HTML file
    webview.create_window('Maprova Projects', html_file, fullscreen=True)
    webview.start()
