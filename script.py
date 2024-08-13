import tkinter as tk
from PIL import Image, ImageTk

# Create the main window
root = tk.Tk()
root.title("Test ImageTk")
root.geometry("800x480")

root.attributes("-fullscreen", True)   

# Path to the images
image_path = "splash.png"
cog_image_path = "cog.png"

# Open the main image
image = Image.open(image_path)

# Set the target height to at least 480 pixels
target_height = 480
image_ratio = image.width / image.height

# Calculate the new dimensions based on the height constraint
new_height = target_height
new_width = int(target_height * image_ratio)

# Resize the main image
image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Convert the image to a format Tkinter can use
photo = ImageTk.PhotoImage(image)

# Create a canvas to hold the image
canvas = tk.Canvas(root, width=800, height=480, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Place the image on the canvas
canvas.create_image(0, 0, anchor="nw", image=photo)

# Load and resize the cog image
cog_image = Image.open(cog_image_path)
cog_image = cog_image.resize((50, 50), Image.Resampling.LANCZOS)
cog_photo = ImageTk.PhotoImage(cog_image)

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

    # Bind all clicks to reset the timer
    root.bind("<Button-1>", reset_timer)

def reset_timer(event=None):
    # Cancel the current timer and start a new 10-second timer
    root.after_cancel(root.after_id)
    root.after_id = root.after(10000, reset_to_initial)

def open_new_window():
    # Clear existing widgets in the root window
    for widget in root.winfo_children():
        widget.destroy()

    # Configure the main window background to #79ff7d
    root.configure(bg="#79ff7d")

    # Create a frame to center the buttons
    frame = tk.Frame(root, bg="#79ff7d")
    frame.pack(expand=True)

    # Set button color to be slightly darker than #04cf5c
    button_bg_color = "#04cf5c"  # A darker shade

    label_1 = tk.Label(frame, text="CPH Village", font=("Arial", 24, "bold"), bg="#79ff7d", fg="black")
    label_1.grid(row=0, column=0, columnspan=2, pady=(20, 0))

    label_2 = tk.Label(frame, text="ME_01.02.04", font=("Arial", 40, "bold"), bg="#79ff7d", fg="black")
    label_2.grid(row=1, column=0, columnspan=2, pady=(0, 20))

    # Create the buttons with additional styling
    btn_print_qr = tk.Button(frame, text="Print QR", font=("Arial", 30, "bold"), bg=button_bg_color, fg="white", padx=70, pady=40, borderwidth=0, highlightthickness=0)
    btn_print_qr.grid(row=2, column=0, pady=20, padx=10)

    btn_choose_qr = tk.Button(frame, text="Vælg QR", font=("Arial", 30, "bold"), bg=button_bg_color, fg="white", padx=70, pady=40, borderwidth=0, highlightthickness=0)
    btn_choose_qr.grid(row=2, column=1, pady=20, padx=10)

    # Center the buttons in the frame
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    # Add the cog button to the bottom right corner
    cog_button = tk.Button(root, image=cog_photo, bg="#79ff7d", borderwidth=0, highlightthickness=0)
    cog_button.image = cog_photo  # Keep a reference to prevent garbage collection
    cog_button.place(relx=1.0, rely=1.0, x=-1, y=-1, anchor="se")

    # Bind all clicks to reset the timer
    root.bind("<Button-1>", reset_timer)

    # Set the initial 10-second timer
    reset_timer()

# Bind the canvas (image) to the click event
canvas.bind("<Button-1>", lambda e: open_new_window())

# Set the initial 10-second timer
root.after_id = root.after(10000, reset_to_initial)

# Start the Tkinter main loop
root.mainloop()
