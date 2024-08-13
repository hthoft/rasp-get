import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
root.title("Test ImageTk")

# Set the window size to 800x480
root.geometry("800x480")
root.attributes('-fullscreen', True)


# Path to the image
image_path = "splash.png"

# Open the image
image = Image.open(image_path)

# Set the target height to at least 480 pixels
target_height = 480
image_ratio = image.width / image.height

# Calculate the new dimensions based on the height constraint
new_height = target_height
new_width = int(target_height * image_ratio)

# Resize the image
image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Convert the image to a format Tkinter can use
photo = ImageTk.PhotoImage(image)

# Create a canvas with the same background color as the image (black, for no edge)
canvas = tk.Canvas(root, width=800, height=480, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Place the image on the canvas (no offsets needed)
canvas.create_image(0, 0, anchor="nw", image=photo)

# Keep a reference to the image to prevent garbage collection
label = tk.Label(root, image=photo)
label.image = photo

# Start the Tkinter main loop
root.mainloop()
