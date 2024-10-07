import requests
from flask import Flask, jsonify, request
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
import qrcode
from PIL import Image, ImageDraw, ImageFont
import subprocess
import socket
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key, customer ID, and printer serial number
api_key = os.getenv('API_KEY')
customer_id = os.getenv('CUSTOMER_ID')
printer_sn = os.getenv('PRINTER_SN')


app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

# Cache Directory and Files
cache_dir = './cache'
projects_cache_file = os.path.join(cache_dir, 'projects_cache.json')
jobs_cache_file = os.path.join(cache_dir, 'jobs_cache.json')

# In-memory cache for projects and jobs
cached_projects = None
cached_jobs = {}

# Create cache directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def custom_encode(number):
    # Convert the number to a hexadecimal string
    hex_string = hex(number)[2:]  # Convert to hex and remove '0x' prefix
    
    # Simple obfuscation: reverse the string and add a salt
    hex_string = hex_string[::-1] + 'salt'
    
    # Further obfuscation: Convert each character to its char code in hex
    obfuscated = ''.join([format(ord(char), 'x') for char in hex_string])
    
    return obfuscated


def handle_print(job_id, job_title, project_title, print_count):
    try:
        def generate_qr_code(data, logo_path, output_path, author, job_title, project_title, max_width_mm):
            # QR code generation code (same as before)
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill='black', back_color='white').convert('RGB')

            # Open the logo image
            logo = Image.open(logo_path)
            max_width_pixels = int(max_width_mm * 300 / 25.4)
            logo_width = max_width_pixels
            logo_height = int(logo.size[1] * (logo_width / logo.size[0]))
            logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

            # Font for the job title
            job_title_font_size = 64
            job_title_font = ImageFont.truetype("arialbd.ttf", job_title_font_size)
            job_title_bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), job_title, font=job_title_font)
            job_title_height = job_title_bbox[3] - job_title_bbox[1]

            # Font for the project title
            project_title_font_size = 40
            project_title_font = ImageFont.truetype("arial.ttf", project_title_font_size)
            project_title_bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), project_title, font=project_title_font)
            project_title_height = project_title_bbox[3] - project_title_bbox[1]

            # Calculate the height based on the contents
            text_space = 150  # Space for the author and timestamp text
            qr_size = max_width_pixels  # QR code should fill the entire width
            total_height = logo_height + job_title_height + project_title_height + qr_size + text_space 

            # Create a new image with the calculated dimensions
            img = Image.new('RGB', (max_width_pixels, total_height), 'white')

            # Paste the logo and QR code onto the new image
            logo_pos = (0, -10)
            img.paste(logo, logo_pos)

            # Draw the job title below the logo
            draw = ImageDraw.Draw(img)
            job_title_pos = ((max_width_pixels - job_title_bbox[2]) // 2, logo_height - 40)
            draw.text(job_title_pos, job_title, font=job_title_font, fill='black')

            project_title_pos = ((max_width_pixels - project_title_bbox[2]) // 2, logo_height + job_title_height - 20)
            draw.text(project_title_pos, project_title, font=project_title_font, fill='black')

            # Draw the QR code below the job title
            qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
            qr_pos = (0, logo_height + job_title_height + project_title_height + 5)
            img.paste(qr_img, qr_pos)

            # Add timestamp and author below the QR code
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            font_size = 36
            font = ImageFont.truetype("arial.ttf", font_size)
            bold_font = ImageFont.truetype("arialbd.ttf", font_size)

            text_author = "Udskrevet af:  "
            text_time = "Udskrevet d.:  "

            author_bbox = draw.textbbox((0, 0), text_author, font=bold_font)
            author_width = author_bbox[2] - author_bbox[0]
            time_bbox = draw.textbbox((0, 0), text_time, font=bold_font)
            time_width = time_bbox[2] - time_bbox[0]

            author_text = f"{text_author} {author}"
            time_text = f"{text_time} {timestamp}"

            total_text_width = max(
                author_width + draw.textbbox((0, 0), author, font=font)[2] - draw.textbbox((0, 0), author, font=font)[0],
                time_width + draw.textbbox((0, 0), timestamp, font=font)[2] - draw.textbbox((0, 0), timestamp, font=font)[0]
            )

            text_pos_y = logo_height + job_title_height + qr_size + 70

            draw.text(((max_width_pixels - total_text_width) // 2, text_pos_y), text_author, fill='black', font=bold_font)
            draw.text(((max_width_pixels - total_text_width) // 2 + author_width, text_pos_y), author, fill='black', font=font)
            draw.text(((max_width_pixels - total_text_width) // 2, text_pos_y + author_bbox[3] + 8), text_time, fill='black', font=bold_font)
            draw.text(((max_width_pixels - total_text_width) // 2 + time_width, text_pos_y + author_bbox[3] + 8), timestamp, fill='black', font=font)

            img.save(output_path, dpi=(300, 300))

        obfuscated_job_id = custom_encode(int(job_id)) 
        # Generate QR code with job_id and job_title
        data = f"{obfuscated_job_id}"  # Use job ID for the QR code data
        logo_path = "dark-logo-white.png"
        #output_path = f"qrcode_{job_id}.png"
        output_path = f"/tmp/qrcode_{job_id}.png"
        author = "Label Printer Hal 7"
        max_width_mm = 62  # Maximum width of the roll in mm
        generate_qr_code(data, logo_path, output_path, author, job_title, project_title, max_width_mm)

        for i in range(print_count):
            print_command = (
                f"sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2042 BROTHER_QL_MODEL=QL-700 "
                f"brother_ql print -l 62 /tmp/qrcode_{job_id}.png"
            )

            result = subprocess.run(print_command, shell=True, capture_output=True, text=True)
            
            # Check for specific error message or warning in the output
            if "Printing potentially not successful" in result.stdout or result.returncode != 0:
                print(f"Warning: Printing potentially not successful on print {i + 1}")
                return False  # Return False if any print job fails

            print(f"Printing {i + 1}/{print_count} QR codes")

        return True  # If everything worked fine

    except subprocess.CalledProcessError as e:
        print(f"Failed to print: {e}")
        return False  # Return False if the print failed
    except Exception as e:
        print(f"Unexpected error: {e}")  # Catch any unexpected errors
        return False  # Handle other unexpected errors




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


# Check if network is available
def is_network_connected():
    try:
        output = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
        return output != ""  # True if connected
    except Exception:
        return False



# Function to fetch all projects
def fetch_all_projects():
    global cached_projects
    url = f"https://portal.maprova.dk/api/getAllProjects.php?apiKey={api_key}&customerID={customer_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    if not is_network_connected():
        print("Network unavailable, using cached project data")
        return load_cached_data(projects_cache_file)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        cached_projects = response.json()  # Cache the response
        save_cached_data(projects_cache_file, cached_projects)  # Save to cache
        return cached_projects
    except requests.RequestException as e:
        print(f"Error fetching projects: {e}")
        return load_cached_data(projects_cache_file)  # Use cached data as fallbackf


# Function to fetch jobs by project ID
def fetch_jobs_by_project(project_id):
    global cached_jobs
    url = f"https://portal.maprova.dk/api/getJobsByProjectID.php?project_id={project_id}&apiKey={api_key}&customerID={customer_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    if not is_network_connected():
        print("Network unavailable, using cached job data")
        cached_jobs = load_cached_data(jobs_cache_file)
        return cached_jobs.get(str(project_id), {})

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        jobs = response.json()

        # Update cached_jobs safely by copying its keys first
        cached_jobs = {**cached_jobs, project_id: jobs}

        save_cached_data(jobs_cache_file, cached_jobs)  # Save to cache
        return jobs
    except requests.RequestException as e:
        print(f"Error fetching jobs for project {project_id}: {e}")
        cached_jobs = load_cached_data(jobs_cache_file)
        return cached_jobs.get(str(project_id), {})  # Use cached data as fallback


# Global flag to track data push status
data_push_status = False

def fetch_and_push_printer_status():
    global data_push_status
    while True:
        try:
            # Collect the local device data
            cpu_temperature = get_cpu_temperature()
            memory_usage = get_memory_usage()
            cpu_usage = get_cpu_usage()
            usb_connected = check_printer_connection()

            # API endpoint for updating printer info
            url = f"https://portal.maprova.dk/api/updateAndGetPrinter.php?apiKey={api_key}&customerID={customer_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # Prepare the payload to send as GET parameters
            payload = {
                'printer_sn': printer_sn,
                'cpu_temperature': cpu_temperature,
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage,
                'usb_connected': int(usb_connected)  # Convert boolean to 0 or 1
            }

            # Send the data as a GET request
            response = requests.get(url, params=payload, headers=headers)

            if response.status_code == 200:
                print(f"Data pushed successfully. Response: {response.json()}")
                data_push_status = True  # Set flag to True on successful push
            else:
                print(f"Failed to push data. Status Code: {response.status_code}")
                data_push_status = False  # Set flag to False if push fails

        except Exception as e:
            print(f"Error pushing printer status: {e}")
            data_push_status = False  # Set flag to False on exception

        # Wait for 60 seconds before the next push
        time.sleep(60)



# Start the thread to fetch and push printer status every 60 seconds
def start_printer_status_pushing():
    thread = threading.Thread(target=fetch_and_push_printer_status)
    thread.daemon = True
    thread.start()


# Flask route to serve project data
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = fetch_all_projects()
    return jsonify(projects)


# Flask route to fetch jobs by project ID
@app.route('/api/jobs/<project_id>', methods=['GET'])
def get_jobs_by_project(project_id):
    jobs = fetch_jobs_by_project(project_id)
    return jsonify(jobs)


@app.route('/api/print', methods=['POST'])
def print_qr_code():
    data = request.get_json()

    job_id = data.get('job_id')
    job_title = data.get('job_title')
    project_title = data.get('project_title')
    print_count = int(data.get('print_count', 1))  # Default to 1 if not provided

    if not job_id or not job_title:
        return jsonify({"status": "error", "message": "Missing job_id or job_title"}), 400

    try:
        print_successful = handle_print(job_id, job_title, project_title, print_count)

        if print_successful:
            return jsonify({"status": "success", "message": "Print job completed successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to print, check printer connection / label roll"}), 500

    except Exception as e:
        print(f"Error occurred during print job: {e}")
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500


@app.route('/api/system_info', methods=['GET'])
def get_system_info():
    ssid, state, ip_address, mac_address = get_network_info()

    printer_connected = check_printer_connection()

    uptime = get_uptime()

    cpu_temp = get_cpu_temperature()

    memory_usage = get_memory_usage()

    cpu_usage = get_cpu_usage()

    push_status = data_push_status

    return jsonify({
        'ssid': ssid,
        'network_state': state,
        'printer_connected': printer_connected,
        'uptime': uptime,
        'cpu_temp': cpu_temp,
        'memory_usage': memory_usage,
        'cpu_usage': cpu_usage,
        'ip_address': ip_address,
        'mac_address': mac_address,
        'push_status': push_status
    })



@app.route('/api/reboot', methods=['POST'])
def reboot_system():
    try:
        # Run the reboot command (this will reboot the Raspberry Pi)
        subprocess.run(['sudo', 'reboot'], check=True)
        return jsonify({"status": "success", "message": "System is rebooting..."}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while rebooting: {e}")
        return jsonify({"status": "error", "message": "Failed to reboot the system", "details": str(e)}), 500

def get_ip_address():
    """
    Get the IP address of the machine (cross-platform).
    """
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "N/A"

def get_mac_address():
    """
    Get the MAC address of the machine (cross-platform).
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
    Returns SSID (if applicable), network state, IP address, and MAC address.
    Cross-platform version.
    """
    try:
        # For Linux, get the SSID
        if platform.system() == "Linux":
            ssid = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
            state = "Connected" if ssid else "Disconnected"
        else:
            # Windows and other platforms
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




def check_printer_connection():
    try:
        if platform.system() == "Linux":
            # This works on Linux (e.g., Raspberry Pi)
            lsusb_output = subprocess.check_output(['lsusb']).decode('utf-8')
            brother_usb_id = "04f9:2042"  # Example of Brother printer USB ID
            return brother_usb_id in lsusb_output
        else:
            # On Windows or other OS, handle differently (lsusb is not available)
            print("USB printer connection check is not supported on this OS.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error checking USB connection: {e}")
        return False

def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    uptime_string = str(timedelta(seconds=uptime_seconds))
    return uptime_string


def get_cpu_temperature():
    if platform.system() == "Linux":
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return temp.split("=")[1].strip()
    return "N/A"

# Function to get memory usage
def get_memory_usage():
    memory_info = psutil.virtual_memory()
    return memory_info.percent  # Return percentage of memory used

# Function to get CPU usage
def get_cpu_usage():
    return psutil.cpu_percent(interval=1)  # Return CPU usage as a percentage

# Function to start Flask in a separate thread
def start_flask():
    app.run(debug=True, host='0.0.0.0', use_reloader=False)


if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start the background task
    start_printer_status_pushing()

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Specify the path to your index.html file
    html_file = os.path.join(current_dir, 'index.html')

    # Create a webview window to open the local HTML file
    webview.create_window('Maprova Projects', html_file, fullscreen=True)
    webview.start()
