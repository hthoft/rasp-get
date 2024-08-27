import hashlib
import requests
import xml.etree.ElementTree as ET
import threading
import os
from flask import Flask, jsonify
from flask_cors import CORS
import time

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

@app.route('/fetch_event_stats')
def fetch_stats():
    print("Received request for /fetch_event_stats")  # Log when the route is hit
    stats = fetch_event_stats()
    print("Returning stats:", stats)  # Log the stats being returned
    return jsonify(stats)


if __name__ == '__main__':
    # Run Flask directly without threading
    app.run(debug=True, host='0.0.0.0')


# Function to check if the Flask server is up and running
def wait_for_server(url, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is up and running.")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    print("Server did not start within the timeout period.")
    return False

# Testing function to call the Flask route and log the result
def test_fetch_stats():
    url = "http://127.0.0.1:5000/fetch_event_stats"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Test fetch stats response:", response.json())
    except requests.RequestException as e:
        print(f"Error during test fetch stats: {e}")
