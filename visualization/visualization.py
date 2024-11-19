import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from flask import Flask, jsonify, request, render_template, send_from_directory
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
# Specify the full path to the .env file
env_path = "/home/RPI-5/.env"

# Load the environment variables from the specified .env file
load_dotenv(dotenv_path=env_path)

# Access the API key, customer ID, and device serial number
api_key = os.getenv('API_KEY')
customer_id = os.getenv('CUSTOMER_ID')
customer_hash = os.getenv('CUSTOMER_HASH')
device_sn = os.getenv('DEVICE_SN')
current_version = os.getenv('CURRENT_VERSION')

# Initialize Flask app and SocketIO
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Cache Directory and Files
cache_dir = './cache'
projects_cache_file = os.path.join(cache_dir, 'projects_cache.json')
jobs_cache_file = os.path.join(cache_dir, 'jobs_cache.json')
departments_cache_file = os.path.join(cache_dir, 'departments_cache.json')
message_cache_file = os.path.join(cache_dir, 'messages_cache.json')

# In-memory cache for projects, jobs, and departments
cached_projects = None
cached_jobs = {}
departments_cache = {}
cached_messages = {}

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
    global cached_projects, cached_jobs, departments_cache, cached_messages

    # Load project cache
    cached_projects = load_cached_data(projects_cache_file)

    # Load jobs cache
    cached_jobs = load_cached_data(jobs_cache_file)

    # Load departments cache
    departments_cache = load_cached_data(departments_cache_file)

    # Load messages cache
    cached_messages = load_cached_data(message_cache_file)


# Save all caches when needed
def save_all_caches():
    # Save project cache
    save_cached_data(projects_cache_file, cached_projects)

    # Save jobs cache
    save_cached_data(jobs_cache_file, cached_jobs)

    # Save departments cache
    save_cached_data(departments_cache_file, departments_cache)

    # Save messages cache
    save_cached_data(message_cache_file, cached_messages)


# Load caches at startup
load_all_caches()


# ============== SocketIO Events ==============



# ============== Update System ==============  
def update_env_version(new_version):
    env_file = '/home/RPI-5/.env'
    
    # Command to update CURRENT_VERSION using sed
    command = f"sudo sed -i 's/^CURRENT_VERSION=.*/CURRENT_VERSION={new_version}/' {env_file}"

    try:
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        print(f".env file updated with new version: {new_version}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update .env file: {e}")


# Main function to check for updates
def check_for_updates():
    global current_version

    while True:
        try:
            # Update check URL
            url = f"https://updates.maprova.dk/checkForUpdate.php?apiKey={api_key}&customerID={customer_id}&systemType=device&currentVersion={current_version}"

            # POST data containing the api_key
            data = {
                'api_key': api_key
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',  # Indicating form-encoded data
                'Accept': 'application/json'  # Expecting JSON response
            }

            # Make the POST request
            response = requests.post(url, headers=headers, data=data)

            if response.status_code == 200:
                data = response.json()

                if data.get('success'):
                    new_version = data['latestVersion']
                    print(f"New update available: {new_version}")

                    # Notify frontend via SocketIO
                    socketio.emit('update_status', {'message': 'Henter opdatering..', 'status': 'downloading'})

                    # Download the update file and replace old files
                    if download_and_replace_update(data['updateFile']):
                        # Update the CURRENT_VERSION in the .env file
                        update_env_version(new_version)

                        # Load the new version into the current environment
                        load_dotenv(dotenv_path='/home/RPI-5/.env')
                        current_version = os.getenv('CURRENT_VERSION')
                        print(f"Current version updated to: {current_version}")
                        socketio.emit('update_status', {'message': 'Opdatering fuldført', 'status': 'success'})

                        # Schedule a reboot in 30 seconds
                        print("Rebooting system in 30 seconds...")
                        time.sleep(30)
                        reboot_system()

                else:
                    print("Already on the latest version.")
            else:
                # Print error response and status code
                print(f"Error checking for updates. Status code: {response.status_code}")
                print(f"Response content: {response.text}")  # Print the response content to inspect

        except Exception as e:
            print(f"Error while checking for updates: {e}")

        # Check again in 1 hour
        time.sleep(30)


import zipfile

def download_and_replace_update(update_url):
    try:
        update_file = "device_update.zip"
        extract_path = "/home/RPI-5/rasp-get/"  # Correct extraction path

        # Download the update file
        print(f"Downloading update from {update_url}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',  # Indicating form-encoded data
            'Accept': 'application/json'  # Expecting JSON response
        }
        response = requests.get(update_url, headers=headers, stream=True)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type')
            if 'text/html' in content_type:
                # It's an HTML page, likely an error or login page
                print("Error: Received an HTML document instead of a zip file.")
                print(response.text)  # Print the HTML response to inspect it
                return

            # Write the content to the file
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Check the file type after downloading
            if zipfile.is_zipfile(update_file):
                print("File is a valid zip file. Extracting and replacing files...")

                # Ensure the extract_path exists
                if not os.path.exists(extract_path):
                    os.makedirs(extract_path)

                # Extract and replace the old files
                with zipfile.ZipFile(update_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # Clean up the zip file
                os.remove(update_file)
                print("Update completed successfully.")
                return True
            else:
                socketio.emit('update_status', {'message': 'Error: The downloaded file is not a valid zip file.', 'status': 'error'})

                print("Error: The downloaded file is not a valid zip file.")

        else:
            socketio.emit('update_status', {'message': f'Failed to download the update. Status code: {response.status_code}', 'status': 'error'})

            print(f"Failed to download the update file. Status code: {response.status_code}")
            print(response.text)  # Print the error response for debugging

    except Exception as e:
        socketio.emit('update_status', {'message': f'Error during update: {e}', 'status': 'error'})

        print(f"Error during update: {e}")


local_pdf_path = "static/current_workload.pdf"

# ============== Routes ==============
@app.route('/')
def index():
    return "Socket.IO server is running!"


@app.route('/visualization')
def visualization():
    """z
    Serve the visualization.html file from the templates directory.
    """
    return render_template('visualization.html')


@app.route('/pdfVisualization')
def pdfVisualization():
    """
    Serve the pdfVisualization.html file from the templates directory.
    """
    return render_template('pdfVisualization.html')



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
    

@app.route('/get_latest_pdf', methods=['GET'])
def get_latest_pdf():
    """
    Find and return the latest PDF file from the static/data directory.
    """
    try:
        fetch_and_update_latest_pdf()
        pdf_directory = os.path.join(app.static_folder, "data")
        pdf_files = [f for f in os.listdir(pdf_directory) if f.startswith("workload-") and f.endswith(".pdf")]

        if not pdf_files:
            return jsonify({"error": "No PDF file found"}), 404

        # Sort files by modification time
        pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(pdf_directory, x)), reverse=True)
        latest_pdf = pdf_files[0]

        # Provide the relative URL for the PDF file
        pdf_url = f"/static/data/{latest_pdf}"
        return jsonify({"pdfPath": pdf_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update_pdf', methods=['GET'])
def update_pdf():
    """
    Endpoint to fetch the latest PDF from the server and update it locally.
    """
    result = fetch_and_update_latest_pdf()
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200


@app.route('/api/get_departments', methods=['GET'])
def get_departments():
    """
    Return the cached department data in JSON format.
    """
    departments_cache = load_cached_data(departments_cache_file)
    return jsonify(departments_cache)

@app.route('/api/get_job_tasks', methods=['GET'])
def get_job_tasks():
    """
    Fetch job tasks from the external API based on department_id, with caching.
    """
    department_id = request.args.get('department_id')

    if not department_id:
        return jsonify({"error": "department_id is required"}), 400

    # External API endpoint to fetch job tasks
    url = f"https://portal.maprova.dk/api/jobTasks/getJobsAndTasks.php"

    # Prepare the payload for the request
    params = {
        'departmentID': department_id,
        'apiKey': api_key,  # Your API key from environment variables
        'customerID': customer_id  # Your customer ID from environment variables
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Send a GET request to the external API
        response = requests.get(url, params=params, headers=headers, timeout=10)

        # If the response is successful, process the data
        if response.status_code == 200:
            job_tasks = response.json()

            # If there's cached data for the department, compare it with the new data
            if department_id in cached_jobs:
                cached_data = cached_jobs[department_id]
                if not data_changed(job_tasks, cached_data):
                    
                    return jsonify(cached_data), 200

            # If data has changed, or if there's no cached data, update the cache
            print(f"Data has changed or no cached data for department {department_id}. Updating cache.")
            cached_jobs[department_id] = job_tasks
            save_cached_data(jobs_cache_file, cached_jobs)  # Save to disk

            return jsonify(job_tasks), 200
        else:
            return jsonify({"error": f"Failed to fetch job tasks, status code: {response.status_code}"}), response.status_code

    except ConnectionError:
        return jsonify({"error": "Failed to connect to the external API"}), 500

    except Timeout:
        return jsonify({"error": "The request to the external API timed out"}), 500

    except RequestException as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    

@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    """
    Fetch messages from the external API with caching and remove expired messages.
    """

    # External API endpoint to fetch job tasks
    url = f"https://portal.maprova.dk/api/messages/getAllMessages.php"

    # Prepare the payload for the request
    params = {
        'apiKey': api_key,  # Your API key from environment variables
        'customerID': customer_id  # Your customer ID from environment variables
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Send a GET request to the external API
        response = requests.get(url, params=params, headers=headers, timeout=10)

        # If the response is successful, cache the data and return it
        if response.status_code == 200:
            messages = response.json()

            # Filter out expired messages
            today = datetime.now().date()
            filtered_messages = [
                message for message in messages 
                if 'message_expire' not in message or datetime.strptime(message['message_expire'], "%Y-%m-%d").date() >= today
            ]

            # Cache the filtered result
            cached_messages = filtered_messages
            save_cached_data(message_cache_file, cached_messages)  # Save to disk

            return jsonify(filtered_messages), 200
        else:
            return jsonify({"error": f"Failed to fetch job tasks, status code: {response.status_code}"}), response.status_code

    except ConnectionError:
        return jsonify({"error": "Failed to connect to the external API"}), 500

    except Timeout:
        return jsonify({"error": "The request to the external API timed out"}), 500

    except RequestException as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/system_info', methods=['GET'])
def get_system_info():
    ssid, state, ip_address, mac_address = get_network_info()

    uptime = get_uptime()

    cpu_temp = get_cpu_temperature()

    memory_usage = get_memory_usage()

    cpu_usage = get_cpu_usage()

    push_status = data_push_status

    return jsonify({
        'ssid': ssid,
        'network_state': state,
        'uptime': uptime,
        'cpu_temp': cpu_temp,
        'memory_usage': memory_usage,
        'cpu_usage': cpu_usage,
        'ip_address': ip_address,
        'mac_address': mac_address,
        'push_status': push_status,
        'serial_number': device_sn
    })

# ============== Device Status and Data Fetching ==============

def fetch_and_update_latest_pdf():
    """
    Fetch the latest PDF from the server and update it locally if necessary.
    """
    # Define directories and API URL
    pdf_directory = os.path.join(app.static_folder, "data")
    remote_api_url = (
        f"https://portal.maprova.dk/actions/getLatestPDF.php"
        f"?apiKey={api_key}&customerID={customer_id}&customerHash={customer_hash}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    # Ensure the directory exists
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    try:
        # Fetch the latest PDF metadata from the remote server
        response = requests.get(remote_api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return {"error": f"Failed to fetch PDF metadata: {response.status_code}"}

        pdf_metadata = response.json()
        if "pdfPath" not in pdf_metadata:
            return {"error": "No valid PDF path returned by the server."}

        # Ensure the PDF URL is absolute
        remote_pdf_url = pdf_metadata["pdfPath"]
        if not remote_pdf_url.startswith("http"):
            remote_pdf_url = f"https://portal.maprova.dk{remote_pdf_url}"

        remote_pdf_name = os.path.basename(remote_pdf_url)

        # Check if the file already exists locally
        local_pdfs = [
            f
            for f in os.listdir(pdf_directory)
            if f.startswith("workload-") and f.endswith(".pdf")
        ]
        local_pdfs.sort(
            key=lambda x: os.path.getmtime(os.path.join(pdf_directory, x)), reverse=True
        )
        local_latest_pdf = local_pdfs[0] if local_pdfs else None

        if local_latest_pdf and remote_pdf_name == local_latest_pdf:
            return {"message": "No updates needed. The latest PDF is already downloaded."}

        # Download the new PDF
        pdf_response = requests.get(remote_pdf_url, stream=True, timeout=10)
        if pdf_response.status_code == 200:
            # Save the new PDF
            remote_pdf_path = os.path.join(pdf_directory, remote_pdf_name)
            with open(remote_pdf_path, "wb") as pdf_file:
                for chunk in pdf_response.iter_content(chunk_size=1024):
                    pdf_file.write(chunk)

            # Remove the old PDFs
            if local_latest_pdf:
                os.remove(os.path.join(pdf_directory, local_latest_pdf))

            return {"message": f"PDF updated successfully: {remote_pdf_name}"}
        else:
            return {"error": f"Failed to download PDF from remote server: {pdf_response.status_code}"}

    except requests.ConnectionError:
        return {"error": "Failed to connect to the remote server."}
    except requests.Timeout:
        return {"error": "Request to the remote server timed out."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

 

def filter_irrelevant_fields(data):
    """
    Remove fields that should not be considered when checking if data has changed.
    """
    # Make a copy of the data to avoid modifying the original
    filtered_data = data.copy()

    # Remove fields that are irrelevant for the comparison, like timestamps
    if 'device_last_update' in filtered_data:
        del filtered_data['device_last_update']

    return filtered_data

def data_changed(new_data, cached_data):
    """
    Compare the filtered new data with the cached data, excluding irrelevant fields.
    """
    # Filter out the irrelevant fields before comparison
    filtered_new_data = filter_irrelevant_fields(new_data)
    filtered_cached_data = filter_irrelevant_fields(cached_data)

    # Compare the two datasets
    return json.dumps(filtered_new_data, sort_keys=True) != json.dumps(filtered_cached_data, sort_keys=True)


def fetch_and_push_device_status():
    """
    Fetch and push device status to external API in intervals with manual retry logic.
    """
    global data_push_status
    max_retries = 5  # Maximum number of retries
    retry_delay = 5  # Time in seconds to wait before retrying

    while True:
        retry_count = 0
        success = False

        # Load the cached device data  
        cached_device_data = load_cached_data(departments_cache_file)

        now = datetime.now()
        if now.hour == 2 and now.minute == 0 and 0 <= now.second <= 20:
            print("Scheduled reboot triggered between 02:00:00 and 02:00:20...")
            os.system("sudo reboot")

        while retry_count < max_retries and not success:
            try:
                # Use a session and close it after each request to force DNS lookup refresh
                with requests.Session() as session:
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
                    response = session.get(url, params=payload, headers=headers, timeout=10)

                    if response.status_code == 200:
                        print ("Data pushed successfully")
                        device_data = response.json()  # Get the device data
                        print (device_data)
                        handle_reboot_flags(device_data)  # Handle reboot if necessary
                        
                        data_push_status = True  # Flag successful push
                        success = True  # Set success to True to break out of the retry loop

                        if data_changed(device_data, cached_device_data):
                            # Update the cache
                            save_cached_data(departments_cache_file, device_data)
                        else:
                            print("No change in data. Cache remains the same.")


                    else:
                        print(f"Error: Failed to push data. Status Code: {response.status_code}")
                        data_push_status = False  # Flag failure

            except ConnectionError:
                print(f"Error: Failed to connect to the server (Attempt {retry_count + 1}/{max_retries}). Retrying...")
                data_push_status = False  # Flag connection error

            except Timeout:
                print(f"Error: The request timed out (Attempt {retry_count + 1}/{max_retries}). Retrying...")
                data_push_status = False  # Flag timeout error

            except RequestException as e:
                print(f"Error: An unexpected error occurred (Attempt {retry_count + 1}/{max_retries}): {e}")
                data_push_status = False  # Flag general request exception

            # Increment the retry count and delay the next attempt if not successful
            retry_count += 1
            if not success and retry_count < max_retries:
                time.sleep(retry_delay)

        # If the loop completes without success, log a failure and move to the next interval
        if not success:
            print(f"Failed to push data after {max_retries} attempts. Moving to the next interval...")

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


def handle_reboot_flags(device_data, device_sn):
    """
    Handle reboot based on the reboot flag from device data.
    """
    reboot_flag = device_data.get('reboot', False)

    if reboot_flag is True:  # Check if reboot is required
        print("Reboot flag is set. Rebooting system...")
        update_reboot_flag(device_sn, 0)  # Update the reboot flag on the server
        reboot_system()
    else:
        print("No reboot required. Reboot flag is not set.")



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
    Returns the current IP address of the system.
    """
    try:
        # Use hostname to retrieve the IP address
        ip_address = subprocess.check_output(["hostname", "-I"]).decode().strip()
        if ip_address:
            return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
    return "N/A"

def get_mac_address():
    """
    Returns the MAC address of the system.
    """
    try:
        # For Linux, get MAC address of eth0 or wlan0
        mac_address = subprocess.check_output(["cat", "/sys/class/net/wlan0/address"]).decode().strip()
        return mac_address
    except Exception as e:
        print(f"Error getting MAC address: {e}")
    return "N/A"

def get_network_info():
    """
    Returns SSID (if applicable), network state, IP address, and MAC address.
    Cross-platform version.
    """
    try:
        # For Linux, get the SSID
        if platform.system() == "Linux":
            try:
                ssid = subprocess.check_output(["iwgetid", "-r"], stderr=subprocess.STDOUT).decode().strip()
                state = "Connected" if ssid else "Disconnected"
            except subprocess.CalledProcessError as e:
                # Handle error if iwgetid is not available or fails
                print(f"Error running iwgetid: {e}")
                ssid = "N/A"
                state = "Disconnected"
        else:
            # Windows or other platforms
            ssid = "N/A"
            state = "Connected"  # Assume connected if IP is obtained

        ip_address = get_ip_address()
        mac_address = get_mac_address()

    except Exception as e:
        ssid = "Error"
        state = "Error"
        ip_address = "N/A"
        mac_address = "N/A"
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
def start_device_status_pushing():
    socketio.start_background_task(target=fetch_and_push_device_status)


# def start_update_checking():
#     socketio.start_background_task(target=check_for_updates)

if __name__ == '__main__':


    start_device_status_pushing()
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
