import hashlib
import subprocess
import xml.etree.ElementTree as ET
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

# Function to generate the sha hash
def generate_hash(version, user, event_id, cash, secret):
    string_to_hash = f"{version}:{user}:{event_id}:{cash}:{secret}"
    return hashlib.sha256(string_to_hash.encode()).hexdigest()

# Function to fetch event stats using curl and subprocess
def fetch_event_stats_with_curl():
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
        # Generate the correct sha hash
        sha_hash = generate_hash(params['version'], params['user'], event_id, params['cash'], params['secret'])

        # Build the URL
        url = f"{host}{endpoints}{event_id}?version={params['version']}&user={params['user']}&cash={params['cash']}&event={event_id}&sha={sha_hash}"

        # Use subprocess to call curl and capture the output
        result = subprocess.run(['curl', '-s', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check if curl was successful
        if result.returncode != 0:
            print(f"Error fetching data for event {event_id}: {result.stderr.decode('utf-8')}")
            counts.append(0)
            continue

        # Print the raw XML response for debugging
        xml_data = result.stdout.decode('utf-8')
        print(f"XML Data for event {event_id}:")
        print(xml_data)

        # Parse the XML response
        try:
            root = ET.fromstring(xml_data)
            count = 0

            # Debugging: Print the structure of the XML
            for ticket in root.findall('.//ticket'):
                print(f"Ticket ID: {ticket.attrib['id']}")
                for price in ticket.findall('.//price'):
                    print(f"Price Amount: {price.find('amount').text}, Count: {price.find('count').text}")
                    count += int(price.find('count').text)

            counts.append(count)
            total_count += count

        except ET.ParseError as e:
            print(f"Error parsing XML for event {event_id}: {e}")
            counts.append(0)

    return {
        "billetter": counts[0],
        "medlemsskaber": counts[1],
        "tutorer": counts[2],
        "total": total_count
    }

@app.route('/fetch_event_stats')
def fetch_stats():
    stats = fetch_event_stats_with_curl()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
