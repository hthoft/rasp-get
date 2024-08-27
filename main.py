import webview
import os
import threading

from flask import Flask, jsonify, render_template
import hashlib
import requests

app = Flask(__name__)

# Function to generate the hash
def generate_hash(string):
    return hashlib.sha256(string.encode()).hexdigest()

@app.route('/fetch_event_stats')
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
        data = response.json()
        
        count = 0
        # Extract count from response data
        # (Assuming response format here. Adjust if needed.)
        if 'tickets' in data:
            for ticket in data['tickets']:
                count += ticket.get('count', 0)
        
        counts.append(count)
        total_count += count

    return jsonify({
        "billetter": counts[0],
        "medlemsskaber": counts[1],
        "tutorer": counts[2],
        "total": total_count
    })

def start_flask():
    app.run(debug=True, use_reloader=False)

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
    webview.create_window('Local Webview Example', html_file, fullscreen=True)
    webview.start()