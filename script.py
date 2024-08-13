import tkinter as tk
from PIL import Image, ImageTk

# Create the main window
root = tk.Tk()
root.title("Test ImageTk")
root.geometry("800x480")

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

# Create a canvas to hold the image
canvas = tk.Canvas(root, width=800, height=480, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Place the image on the canvas
canvas.create_image(0, 0, anchor="nw", image=photo)

# Function to open a new window with two buttons
def open_new_window():
    new_window = tk.Toplevel(root)
    new_window.title("New Window")
    new_window.geometry("800x480")
    new_window.configure(bg="black")

    btn_print_qr = tk.Button(new_window, text="Print QR", font=("Helvetica", 28), bg="white", fg="black")
    btn_print_qr.pack(pady=20)

    btn_choose_qr = tk.Button(new_window, text="Vælg QR", font=("Helvetica", 28), bg="white", fg="black")
    btn_choose_qr.pack(pady=20)

# Bind the canvas (image) to the click event
canvas.bind("<Button-1>", lambda e: open_new_window())

# Start the Tkinter main loop
root.mainloop()
