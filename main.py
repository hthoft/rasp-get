import webview
import os

if __name__ == '__main__':
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Specify the path to your index.html file
    html_file = os.path.join(current_dir, 'index.html')

    # Create a webview window and open in fullscreen mode
    webview.create_window('Local Webview Example', html_file, fullscreen=True)

    # Start the webview
    webview.start()
