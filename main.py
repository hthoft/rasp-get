import webview
import sys

# Override print function to avoid errors
def custom_print(*args, **kwargs):
    pass

# Temporarily replace the print function
original_print = print
print = custom_print

if __name__ == '__main__':
    # Your webview code here
    webview.create_window('Hello World', 'https://www.example.com')
    webview.start()

# Restore the original print function
print = original_print
