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
#env_path = "C:\\Users\\Hans Thoft Rasmussen\\Documents\\GitHub\\rasp-get\\.env"

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

# Max cache size in bytes (e.g., 10 MB)
MAX_CACHE_SIZE = 10 * 1024 * 1024  # 10 MB

# Check if cache size exceeds the maximum allowed size
def is_cache_too_large():
    """
    Check if the total size of all cache files exceeds the defined maximum size.
    """
    total_size = 0
    for filename in [projects_cache_file, jobs_cache_file, departments_cache_file, message_cache_file]:
        if os.path.exists(filename):
            total_size += os.path.getsize(filename)
    return total_size > MAX_CACHE_SIZE


def clean_up_cache():
    """
    Remove the least recently used (LRU) cache entries when the total cache size exceeds the limit.
    """
    global cached_projects, cached_jobs, departments_cache, cached_messages

    print("Cache size exceeded. Cleaning up cache...")

    # Prioritize cache cleanup (start with the least critical data)
    cached_jobs.clear()  # Clear jobs cache first
    save_cached_data(jobs_cache_file, cached_jobs)

    # If still too large, clear other caches
    if is_cache_too_large():
        cached_projects = {}
        save_cached_data(projects_cache_file, cached_projects)

    if is_cache_too_large():
        departments_cache = {}
        save_cached_data(departments_cache_file, departments_cache)

    if is_cache_too_large():
        cached_messages = {}
        save_cached_data(message_cache_file, cached_messages)


def save_cached_data(filename, data):
    """
    Save data to a cache file while ensuring size limits.
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving cache to {filename}: {e}")


def load_cached_data(filename):
    """
    Load data from a cache file, returning an empty dictionary if not found or invalid.
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from cache file {filename}: {e}")
    return {}


def load_all_caches():
    """
    Load all cache files into memory. Perform cleanup if cache size exceeds limits.
    """
    global cached_projects, cached_jobs, departments_cache, cached_messages

    # Load project cache
    cached_projects = load_cached_data(projects_cache_file)

    # Load jobs cache
    cached_jobs = load_cached_data(jobs_cache_file)

    # Load departments cache
    departments_cache = load_cached_data(departments_cache_file)

    # Load messages cache
    cached_messages = load_cached_data(message_cache_file)

    # Perform cleanup if cache size exceeds the limit
    if is_cache_too_large():
        clean_up_cache()


def save_all_caches():
    """
    Save all in-memory cache data to their respective files.
    """
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



def sync_files(base_url, local_base_path, files_and_dirs, metadata_filename="metadata.json"):
    """
    Synchronize files between a server and a local directory.

    Args:
        base_url (str): Base URL of the hosted directory.
        local_base_path (str): Local directory to save the files.
        files_and_dirs (list): List of files and directories to synchronize.
        metadata_filename (str): Filename for the metadata file (default: 'metadata.json').

    Returns:
        str: Status message indicating the result of the synchronization.
    """
    # Path to the metadata file
    metadata_file = os.path.join(local_base_path, metadata_filename)

    # Headers with a User-Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Load existing metadata
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                print("Corrupt metadata file detected. Re-downloading all files.")
                metadata = {}

    # Track if any changes were made
    changes_made = False

    # Function to download and save a file
    def download_file(file_url, local_path, relative_path):
        nonlocal changes_made
        file_headers = headers.copy()

        # Add If-None-Match and If-Modified-Since headers if available
        if relative_path in metadata:
            if "etag" in metadata[relative_path]:
                file_headers["If-None-Match"] = metadata[relative_path]["etag"]
            if "last_modified" in metadata[relative_path]:
                file_headers["If-Modified-Since"] = metadata[relative_path]["last_modified"]

        # Make the request
        response = requests.get(file_url, headers=file_headers)
        if response.status_code == 200:
            # Save the file
            with open(local_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {file_url} -> {local_path}")

            # Update metadata and mark changes
            metadata[relative_path] = {
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
            changes_made = True
        elif response.status_code == 304:
            print(f"No changes for: {file_url}")
        elif response.status_code == 404:
            print(f"File not found on server: {file_url}")
        else:
            print(f"Failed to download: {file_url} (Status code: {response.status_code})")

    # Ensure local directory structure exists
    for relative_path in files_and_dirs:
        local_file_path = os.path.join(local_base_path, relative_path)
        local_dir = os.path.dirname(local_file_path)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

    # Step 1: Validate and clean up local files
    for relative_path in list(metadata.keys()):
        local_path = os.path.join(local_base_path, relative_path)
        if relative_path not in files_and_dirs or not os.path.exists(local_path):
            print(f"Removing outdated file or metadata: {local_path}")
            metadata.pop(relative_path, None)
            if os.path.exists(local_path):
                os.remove(local_path)
            changes_made = True

    # Step 2: Synchronize files
    for relative_path in files_and_dirs:
        local_path = os.path.join(local_base_path, relative_path)
        file_url = f"{base_url}{relative_path}"
        download_file(file_url, local_path, relative_path)

    # Step 3: Save updated metadata
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)

    # Final message
    if not changes_made:
        return "No changes have been made."
    else:
        return "Synchronization completed successfully."


def syncCall():
    """
    Initiates the synchronization process by providing the necessary parameters.
    """
    # Get the customer hash from the environment
    customer_hash = os.getenv("CUSTOMER_HASH")

    # Validate that the customer_hash exists
    if not customer_hash:
        print("Customer hash is not set in the environment variables.")
        return

    # Define the base URL with the customer hash
    base_url = f"https://updates.maprova.dk/visualization/{customer_hash}/"

    # Local path to save files
    local_base_path = "./"

    # List of files and directories to sync
    files_and_dirs = [
        "static/css/bootstrap.min.css",
        "static/css/sweetalert-dark.css",
        "static/css/view_style.css",
        "static/css/visualization.min.css",
        "static/images/dark-logo.png",
        "static/images/maprova-bg.png",
        "static/js/bootstrap.bundle.min.js",
        "static/js/jquery-3.6.0.min.js",
        "static/js/socket.io.js",
        "static/js/sweetalert.js",
        "static/js/view_script.js",
        "templates/pdfVisualization.html",
        "templates/visualization.html",
    ]

    # Call the sync function
    status = sync_files(base_url, local_base_path, files_and_dirs)
    print(status)


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
    Fetch job tasks from the external API based on department_id, with in-memory caching.
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

            # Cache the new data in memory
            print(f"Caching new data for department {department_id}")
            cached_jobs[department_id] = job_tasks

            return jsonify(job_tasks), 200
        else:
                    # If there's cached data for the department, return it
            if department_id in cached_jobs:
                cached_data = cached_jobs[department_id]
                print(f"Serving cached data for department {department_id}")
                return jsonify(cached_data), 200
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
                        handle_reboot_flags(device_data, device_sn)  # Handle reboot if necessary
                        
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
    syncCall()


    start_device_status_pushing()
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
