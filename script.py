import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
root.title("Test ImageTk")

# Set the window size to 800x480
root.geometry("800x480")

# Path to the image
image_path = "splash.png"

# Open the image
image = Image.open(image_path)

# Calculate the appropriate size to maintain aspect ratio
max_width, max_height = 800, 480
image_ratio = image.width / image.height
window_ratio = max_width / max_height

if image_ratio > window_ratio:
    # Image is wider relative to its height; fit to width
    new_width = max_width
    new_height = int(max_width / image_ratio)
else:
    # Image is taller relative to its width; fit to height
    new_width = int(max_height * image_ratio)
    new_height = max_height

# Resize the image while maintaining the aspect ratio
image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Convert the image to a format Tkinter can use
photo = ImageTk.PhotoImage(image)

# Display the image in a label widget
label = tk.Label(root, image=photo)
label.image = photo  # Keep a reference to prevent garbage collection
label.pack(expand=True)

# Start the Tkinter main loop
root.mainloop()
