from flask import Flask, render_template
import webview
import threading
import os

# Initialize Flask app
app = Flask(__name__)

# ============== Routes ==============
@app.route('/')
def index():
    """
    Serve the qr_display.html file.
    """
    return render_template('qr_scan.html')

# ============== Flask and Webview Initialization ==============
def run_flask():
    """
    Run Flask server.
    """
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    # Start Flask server in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Get the current directory and specify the path to qr_display.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, 'qr_scan.html')

    # Create a WebView window to open the local HTML file
    webview.create_window('QR Code Display', html_file, fullscreen=True)
    webview.start()
