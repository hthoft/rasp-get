import hashlib
import requests
import xml.etree.ElementTree as ET
import threading
import os
import webview
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

# Function to generate the hash
def generate_hash(string):
    return hashlib.sha256(string.encode()).hexdigest()

# Function to fetch event stats from the Safeticket API
def fetch_event_stats():
    event_ids = ["100534", "100541", "100963"]
    total_tickets = 6000
    total_count = 0

    host = "https://studentersamfundet.safeticket.dk/api/"
    params = {
        'version': 1,
        'user': "ssf_sales",
        'secret': "91a03fad61159e49c99f63dc944ab04d36c5640a5354ef4266b2d39329d25fd3",
        'cash': 1
    }
    endpoints = "stats/"

    counts = []
    for event_id in event_ids:
        hash_string = f"{params['version']}:{params['user']}:{event_id}:{params['cash']}:{params['secret']}"
        hash_value = generate_hash(hash_string)
        url = f"{host}{endpoints}{event_id}?version={params['version']}&user={params['user']}&cash={params['cash']}&event={event_id}&sha={hash_value}"
        
        response = requests.get(url)
        print(f"Response from {url}: {response.status_code}, {response.text[:100]}...")  # Truncate for brevity
        
        # Parse the XML response
        try:
            root = ET.fromstring(response.text)
            count = 0

            # Iterate over tickets and sum their counts
            for ticket in root.findall('.//ticket'):
                for price in ticket.findall('.//price'):
                    count += int(price.find('count').text)

            counts.append(count)
            total_count += count

        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            counts.append(0)

    return {
        "billetter": counts[0],
        "medlemsskaber": counts[1],
        "tutorer": counts[2],
        "total": total_count
    }

# Flask route to serve event stats
@app.route('/fetch_event_stats')
def fetch_stats():
    stats = fetch_event_stats()
    return jsonify(stats)

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
    webview.create_window('Event Stats', html_file, fullscreen=True)
    webview.start()
