import tkinter as tk
from PIL import Image, ImageTk

# Create the main window
root = tk.Tk()
root.title("Test ImageTk")
root.geometry("800x480")

root.attributes("-fullscreen", True)   

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

# Function to reset to the initial state
def reset_to_initial():
    # Clear existing widgets in the root window
    for widget in root.winfo_children():
        widget.destroy()

    # Recreate the canvas and place the image again
    canvas = tk.Canvas(root, width=800, height=480, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=photo)

    # Rebind the click event
    canvas.bind("<Button-1>", lambda e: open_new_window())

def open_new_window():
    # Clear existing widgets in the root window
    for widget in root.winfo_children():
        widget.destroy()

    # Configure the main window background to #04c5cf
    root.configure(bg="#04c5cf")

    # Create a frame to center the buttons
    frame = tk.Frame(root, bg="#04cf5c")
    frame.pack(expand=True)

    # Set button color to be slightly darker than #04c5cf
    button_bg_color = "#039b9e"  # A darker shade

    # Create the buttons with additional styling
    btn_print_qr = tk.Button(frame, text="Print QR", font=("Helvetica", 28, "bold"), bg=button_bg_color, fg="black", padx=20, pady=10, borderwidth=0, highlightthickness=0)
    btn_print_qr.grid(row=0, column=0, pady=20)

    btn_choose_qr = tk.Button(frame, text="Vælg QR", font=("Helvetica", 28, "bold"), bg=button_bg_color, fg="black", padx=20, pady=10, borderwidth=0, highlightthickness=0)
    btn_choose_qr.grid(row=1, column=0, pady=20)

    # Center the buttons in the frame
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    # Set a timer to reset to the initial state after 10 seconds
    root.after(10000, reset_to_initial)

# Bind the canvas (image) to the click event
canvas.bind("<Button-1>", lambda e: open_new_window())

# Start the Tkinter main loop
root.mainloop()
