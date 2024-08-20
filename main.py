import webview
import sys

# Override print function to avoid errors
def custom_print(*args, **kwargs):
    pass

# Temporarily replace the print function
sys.stdout.write = custom_print

if __name__ == '__main__':
    webview.create_window('Hello World', 'https://www.example.com')
    webview.start()

# Restore the original stdout write function
sys.stdout.write = sys.__stdout__.write
