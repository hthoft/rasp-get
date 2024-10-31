from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import serial
import os

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Replace with the actual port and baudrate of your scanner
SERIAL_PORT = "/dev/ttyUSB0"  # Adjust as necessary for your system
BAUDRATE = 9600

def listen_to_scanner():
    """Listen for scanned input from the serial port and emit events to the frontend."""
    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE) as ser:
            scan_buffer = ""  # To accumulate scanned data
            while True:
                char = ser.read().decode("utf-8")  # Read each character
                if char == "\n":  # Detect newline (Enter) from scanner
                    # Send the scan result to the frontend
                    socketio.emit("scan_success", {"scan_id": scan_buffer})
                    print(f"Scan complete: {scan_buffer}")
                    scan_buffer = ""  # Clear buffer for the next scan
                else:
                    scan_buffer += char  # Accumulate characters
    except Exception as e:
        print(f"Error reading from scanner: {e}")

# Flask route
@app.route("/")
def index():
    """Serve the main HTML file."""
    return render_template("qr_scan.html")

if __name__ == "__main__":
    # Start listening to the scanner in a background thread
    threading.Thread(target=listen_to_scanner, daemon=True).start()
    
    # Run Flask app with SocketIO
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
