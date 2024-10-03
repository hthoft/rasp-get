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

            subprocess.run(print_command, shell=True, check=True)
            print(f"Printing {i + 1}/{print_count} QR codes")

        return True  # If everything worked fine

    except subprocess.CalledProcessError as e:
        print(f"Failed to print: {e}")
        return False  # Return False if the print failed
    except Exception as e:
        print(f"Unexpected error: {e}")  # Catch any unexpected errors
        return False  # Handle other unexpected errors



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
        # Log the exact error details
        print(f"Error occurred during print job: {e}")
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500


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
