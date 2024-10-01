import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import os
import webview

app = Flask(__name__)
CORS(app)  # Apply CORS to the entire app

import qrcode
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import subprocess

def handle_print(job_id, job_title, print_count):
    def generate_qr_code(data, logo_path, output_path, author, max_width_mm):
        # Generate QR code
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

        # Calculate the height based on the contents
        text_space = 50  # Space for the text
        qr_size = max_width_pixels  # QR code should fill the entire width
        total_height = logo_height + qr_size + text_space

        # Create a new image with the calculated dimensions
        img = Image.new('RGB', (max_width_pixels, total_height), 'white')

        # Paste the logo and QR code onto the new image
        logo_pos = (-15, 0)
        img.paste(logo, logo_pos)

        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
        qr_pos = (-15, logo_height)
        img.paste(qr_img, qr_pos)

        # Add timestamp and author
        draw = ImageDraw.Draw(img)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        font_size = 24
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

        text_pos_y = logo_height + qr_size - 10

        draw.text(((max_width_pixels - total_text_width) // 2, text_pos_y), text_author, fill='black', font=bold_font)
        draw.text(((max_width_pixels - total_text_width) // 2 + author_width, text_pos_y), author, fill='black', font=font)
        draw.text(((max_width_pixels - total_text_width) // 2, text_pos_y + author_bbox[3] + 5), text_time, fill='black', font=bold_font)
        draw.text(((max_width_pixels - total_text_width) // 2 + time_width, text_pos_y + author_bbox[3] + 5), timestamp, fill='black', font=font)

        img.save(output_path, dpi=(300, 300))

    # Generate QR code with job_id and job_title
    data = f"{job_id} - {job_title}"  # Use job ID and title for the QR code data
    logo_path = "dark-logo-white.png"
    output_path = f"/tmp/qrcode_{job_id}.png"
    author = "Jens Haldrup"
    max_width_mm = 62  # Maximum width of the roll in mm
    generate_qr_code(data, logo_path, output_path, author, max_width_mm)

    # Print the QR code as many times as specified by print_count
    for i in range(print_count):
        print_command = (
            f"sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2042 BROTHER_QL_MODEL=QL-700 "
            f"brother_ql print -l 62 {output_path}"
        )

        try:
            subprocess.run(print_command, shell=True, check=True)
            print(f"Printing {i + 1}/{print_count} QR codes")
        except subprocess.CalledProcessError as e:
            print(f"Failed to print on iteration {i + 1}: {e}")
            break


# Function to fetch all projects
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

# Function to fetch jobs by project ID
def fetch_jobs_by_project(project_id):
    api_key = '7fd67c060bff8fad72e3b82206d3e49020727b214e1b5bf7cf9df3ceb9a28f44'
    customer_id = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    url = f"https://portal.maprova.dk/api/getJobsByProjectID.php?project_id={project_id}&apiKey={api_key}&customerID={customer_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching jobs for project {project_id}: {e}")
        return {}

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


# Flask route to print a test QR code
@app.route('/api/print', methods=['POST'])
def print_qr_code():
    # Define the function to handle the test print
    def test_print():
        # Generate a simple QR code or print message for testing purposes
        data = "Test Print QR"  # Hardcoded test data for the QR code
        logo_path = "dark-logo-white.png"  # Path to your logo
        output_path = "/tmp/test_qrcode.png"  # Output path for the test image
        author = "Test User"  # Hardcoded author name for the test
        max_width_mm = 62  # Maximum width of the label in mm
        
        # Call the function to generate the QR code with the test data
        handle_print(data, "Test Job", 1)  # Use handle_print with a simple test

        # Print the generated test QR code
        print_command = (
            f"sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2042 "
            f"BROTHER_QL_MODEL=QL-700 brother_ql print -l 62 {output_path}"
        )

        try:
            subprocess.run(print_command, shell=True, check=True)
            print("Test QR code printed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to print test QR code: {e}")
    
    # Call the test print function
    test_print()

    return jsonify({"status": "success", "message": "Test print started"}), 200



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
