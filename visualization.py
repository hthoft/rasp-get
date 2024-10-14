import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

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
import socket
import uuid
from dotenv import load_dotenv

# ============== Environment and Global Variables ==============
# Load environment variables from .env file
load_dotenv()

# Access the API key, customer ID, and device serial number
api_key = os.getenv('API_KEY')
customer_id = os.getenv('CUSTOMER_ID')
device_sn = os.getenv('DEVICE_SN')

# Initialize Flask app and SocketIO
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Cache Directory and Files
cache_dir = './cache'
projects_cache_file = os.path.join(cache_dir, 'projects_cache.json')
jobs_cache_file = os.path.join(cache_dir, 'jobs_cache.json')
departments_cache_file = os.path.join(cache_dir, 'departments_cache.json')

# In-memory cache for projects, jobs, and departments
cached_projects = None
cached_jobs = {}
departments_cache = {}

# Create cache directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Save data to cache
def save_cached_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


# Load data from cache
def load_cached_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


# Load all caches on startup
def load_all_caches():
    global cached_projects, cached_jobs, departments_cache

    # Load project cache
    cached_projects = load_cached_data(projects_cache_file)

    # Load jobs cache
    cached_jobs = load_cached_data(jobs_cache_file)

    # Load departments cache
    departments_cache = load_cached_data(departments_cache_file)


# Save all caches when needed
def save_all_caches():
    # Save project cache
    save_cached_data(projects_cache_file, cached_projects)

    # Save jobs cache
    save_cached_data(jobs_cache_file, cached_jobs)

    # Save departments cache
    save_cached_data(departments_cache_file, departments_cache)


# Load caches at startup
load_all_caches()

# ============== Routes ==============
@app.route('/')
def index():
    return "Socket.IO server is running!"


@app.route('/api/reboot', methods=['POST'])
def reboot_system():
    """
    Route to perform system reboot.
    """
    try:
        subprocess.run(['sudo', 'reboot'], check=True)
        return jsonify({"status": "success", "message": "System is rebooting..."}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while rebooting: {e}")
        return jsonify({"status": "error", "message": "Failed to reboot the system", "details": str(e)}), 500
    

@app.route('/get_departments', methods=['GET'])
def get_departments():
    """
    Return the cached department data in JSON format.
    """
    global departments_cache
    return jsonify(departments_cache)



# ============== Device Status and Data Fetching ==============
def fetch_and_push_device_status():
    """
    Fetch and push device status to external API in intervals.
    """
    global data_push_status

    while True:
        try:
            # Collect the local device data
            cpu_temperature = float(get_cpu_temperature())  # Ensure it's a float
            memory_usage = get_memory_usage()
            cpu_usage = get_cpu_usage()

            # API endpoint for updating device info
            url = f"https://portal.maprova.dk/api/devices/updateAndGetDevice.php?device_sn={device_sn}&apiKey={api_key}&customerID={customer_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            payload = {
                'cpu_temperature': cpu_temperature,
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage,
            }

            # Send the request to fetch the device status with a timeout
            response = requests.get(url, params=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                device_data = response.json()  # Get the device data
                handle_reboot_flags(device_data)  # Handle reboot if necessary
                print(response.json())  # Print the device data
                data_push_status = True  # Flag successful push
            else:
                print(f"Failed to push data. Status Code: {response.status_code}")
                data_push_status = False  # Flag failure

        except ConnectionError:
            print("Error: Failed to connect to the server. Please check your network connection.")
            data_push_status = False  # Flag connection error

        except Timeout:
            print("Error: The request timed out. Retrying...")
            data_push_status = False  # Flag timeout error

        except RequestException as e:
            print(f"Error: An unexpected error occurred: {e}")
            data_push_status = False  # Flag general request exception

        # Wait before the next push
        time.sleep(30)


def update_department_cache(device_data):
    """
    Update the global department cache and save it to a file.
    """
    global departments_cache

    # Update the cache with department IDs
    departments_cache = {
        'department_view_1': device_data.get('department_view_1'),
        'department_view_2': device_data.get('department_view_2'),
        'department_view_3': device_data.get('department_view_3'),
    }

    # Save to file for persistence
    save_cached_data(departments_cache_file, departments_cache)


def handle_reboot_flags(device_data):
    """
    Handle reboot based on the reboot flag from device data.
    """
    reboot_flag = int(device_data.get('reboot_flag', 0))

    if reboot_flag == 2:
        print("Reboot flag is set to 2. Rebooting system...")
        update_reboot_flag(device_sn, 1)
        reboot_system()

    elif reboot_flag == 1:
        print("Reboot flag is set to 1. Confirming the reboot...")
        update_reboot_flag(device_sn, 0)

    elif reboot_flag == 3:
        print("Reboot flag is set to 3. Shutting down for update and rebooting...")
        update_reboot_flag(device_sn, 1)
        run_update_script()


def update_reboot_flag(device_sn, new_flag):
    """
    Update the reboot flag via the API.
    """
    try:
        url = f"https://portal.maprova.dk/api/devices/updateRebootFlag.php?device_sn={device_sn}&new_reboot_flag={new_flag}&apiKey={api_key}&customerID={customer_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"Reboot flag updated to {new_flag} successfully")
        else:
            print(f"Failed to update reboot flag. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error updating reboot flag: {e}")


def run_update_script():
    """
    Run the update script.
    """
    try:
        subprocess.Popen(
            ["bash", "/home/RPI-5/rasp-get/update.sh"],
            stdout=subprocess.PIPE,  # Redirect output to console
            stderr=subprocess.PIPE,  # Redirect errors to console
            shell=False
        )
        print("Update script executed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Error message: {e.stderr.decode()}")


# ============== Utility Functions ==============
def get_ip_address():
    """
    Get the IP address of the machine.
    """
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "N/A"


def get_mac_address():
    """
    Get the MAC address of the machine.
    """
    try:
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                for elements in range(0, 2*6, 8)][::-1])
        return mac_address
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return "N/A"


def get_network_info():
    """
    Returns network details like SSID, network state, IP address, and MAC address.
    """
    try:
        if platform.system() == "Linux":
            ssid = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
            state = "Connected" if ssid else "Disconnected"
        else:
            ssid = "N/A"
            state = "Connected"

        ip_address = get_ip_address()
        mac_address = get_mac_address()

    except Exception as e:
        ssid, state, ip_address, mac_address = "Error", "Error", "N/A", "N/A"
        print(f"Error in get_network_info: {e}")

    return ssid, state, ip_address, mac_address


def check_device_connection():
    """
    Check if the device is connected via USB (for Linux systems).
    """
    try:
        if platform.system() == "Linux":
            lsusb_output = subprocess.check_output(['lsusb']).decode('utf-8')
            brother_usb_id = "04f9:2042"  # Example USB ID
            return brother_usb_id in lsusb_output
        else:
            print("USB device connection check is not supported on this OS.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking USB connection: {e}")
        return False


def get_uptime():
    """
    Get system uptime in human-readable format.
    """
    uptime_seconds = int(time.time() - psutil.boot_time())
    return str(timedelta(seconds=uptime_seconds))


def get_cpu_temperature():
    """
    Get CPU temperature (Linux only).
    """
    if platform.system() == "Linux":
        try:
            temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode().strip()
            return float(temp.split("=")[1].replace("'C", "").strip())
        except Exception as e:
            print(f"Error getting CPU temperature: {e}")
            return 0.0
    return 0.0


def get_memory_usage():
    """
    Get memory usage percentage.
    """
    return psutil.virtual_memory().percent


def get_cpu_usage():
    """
    Get CPU usage percentage.
    """
    return psutil.cpu_percent(interval=1)


# ============== Flask and Webview Initialization ==============
def run_flask():
    """
    Run Flask server with SocketIO.
    """
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)

def start_device_status_pushing():
    socketio.start_background_task(target=fetch_and_push_device_status)


if __name__ == '__main__':
    # Start Flask server in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start the device status pushing thread
    start_device_status_pushing()

    # Get the current directory and specify the path to index.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, 'visualization.html')

    # Create a WebView window to open the local HTML file
    webview.create_window('Maprova Projects', html_file, fullscreen=False)
    webview.start()
