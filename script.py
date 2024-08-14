import tkinter as tk
from PIL import Image, ImageTk
import subprocess

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

def open_print_window():
    # Stop the current timer
    reset_timer()

    # Create a top-level window for the print options
    print_window = tk.Toplevel(root)
    print_window.title("Print QR Codes")
    print_window.geometry("800x480")
    print_window.configure(bg="#86f08a")  # A slightly darker green background

    # Remove the window title bar and center the window
    print_window.overrideredirect(True)
    print_window.update_idletasks()
    width = print_window.winfo_width()
    height = print_window.winfo_height()
    x = (print_window.winfo_screenwidth() // 2) - (width // 2)
    y = (print_window.winfo_screenheight() // 2) - (height // 2)
    print_window.geometry(f'{width}x{height}+{x}+{y}')

    # Function to update the count label and reset the timer
    def update_count(delta):
        reset_timer()  # Reset the timer when plus or minus is clicked
        new_value = int(count_label['text']) + delta
        if 1 <= new_value <= 4:
            count_label.config(text=str(new_value))

    def handle_print():
        # Load the image using PIL
        image_path = "qrcode_with_logo.png"  # Replace with your image path
        image = Image.open(image_path)

        # Save the image as a temporary file (if needed)
        temp_image_path = "/tmp/temp_image.png"
        image.save(temp_image_path)

        # Get the count of how many times to print
        try:
            print_count = int(count_label['text'])  # Assuming count_label contains the desired print count
        except ValueError:
            print("Invalid print count. Using default value of 1.")
            print_count = 1

        # Loop to print the specified number of times
        for i in range(print_count):
            print_command = (
                "sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2043 BROTHER_QL_MODEL=QL-710W "
                f"brother_ql print -l 62 {temp_image_path}"
            )

            try:
                subprocess.run(print_command, shell=True, check=True)
                print(f"Printing {i+1}/{print_count} QR codes")
            except subprocess.CalledProcessError as e:
                print(f"Failed to print on iteration {i+1}: {e}")
                break  # Exit loop on failure

        # Close the print window and reset the timer
        print_window.destroy()
        reset_timer()


    # Function to handle the close action
    def close_window():
        print_window.destroy()
        reset_timer()  # Start the timer again after closing the print window

    # Vertical padding to center the content within the 480px height
    content_height = 280  # Approximate combined height of label, counter frame, and button frame
    padding_top = (480 - content_height) // 2

    # Add a label above the buttons
    instruction_label = tk.Label(print_window, text="Vælg antal:", font=("Arial", 28, "bold"), bg="#86f08a", fg="black")
    instruction_label.pack(pady=(padding_top, 20))

    # Create a frame for the counter and buttons
    counter_frame = tk.Frame(print_window, bg="#86f08a")
    counter_frame.pack(pady=20)

    # Create the minus button
    minus_button = tk.Button(counter_frame, text="-", font=("Arial", 42, "bold"), command=lambda: update_count(-1), bg="green", width=4, height=1, fg="white", padx=30, pady=20, borderwidth=0)
    minus_button.grid(row=0, column=1, padx=20)

    # Create the count label
    count_label = tk.Label(counter_frame, text="1", font=("Arial", 36), bg="white", fg="black", width=4, height=2)
    count_label.grid(row=0, column=2, padx=20)

    # Create the plus button
    plus_button = tk.Button(counter_frame, text="+", font=("Arial", 42, "bold"), command=lambda: update_count(1), bg="green", width=4, height=1, fg="white", padx=30, pady=20, borderwidth=0)
    plus_button.grid(row=0, column=3, padx=20)

    # Configure grid to center the elements
    counter_frame.grid_columnconfigure(0, weight=1)
    counter_frame.grid_columnconfigure(4, weight=1)

    # Create a frame for the print and close buttons
    button_frame = tk.Frame(print_window, bg="#86f08a")
    button_frame.pack(pady=20)

    # Create the red X button to close the window
    close_button = tk.Button(button_frame, text="X", font=("Arial", 36), command=close_window, bg="red", fg="white", padx=20, pady=20, borderwidth=0, width=3)
    close_button.grid(row=0, column=0, padx=10, sticky="ew")

    # Create the green print button
    print_button = tk.Button(button_frame, text="Print", font=("Arial", 36), command=handle_print, bg="green", fg="white", padx=20, pady=20, borderwidth=0)
    print_button.grid(row=0, column=1, padx=10, sticky="ew")

    # Configure grid to set the 20:80 width ratio
    button_frame.grid_columnconfigure(0, weight=2)  # 20% width for the close button
    button_frame.grid_columnconfigure(1, weight=8)  # 80% width for the print button

    # Set a fixed height for the button frame to ensure the buttons have height
    button_frame.update_idletasks()
    button_frame_height = close_button.winfo_reqheight()
    button_frame.config(height=button_frame_height)


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
    btn_print_qr = tk.Button(frame, text="Print QR", font=("Arial", 30, "bold"), bg=button_bg_color, fg="white", padx=70, pady=40, borderwidth=0, highlightthickness=0, command=open_print_window)
    btn_print_qr.grid(row=2, column=0, pady=20, padx=10)

    btn_choose_qr = tk.Button(frame, text="Vælg QR", font=("Arial", 30, "bold"), bg=button_bg_color, fg="white", padx=70, pady=40, borderwidth=0, highlightthickness=0)
    btn_choose_qr.grid(row=2, column=1, pady=20, padx=10)

    # Center the buttons in the frame
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Define the status dot color (choose from "green", "red", or "yellow")
    status_color = "red"  # Example color

    # Create a canvas for the status dot
    status_dot = tk.Canvas(root, width=12, height=12, bg="#79ff7d", highlightthickness=0)
    dot_id = status_dot.create_oval(2, 2, 10, 10, fill=status_color, outline=status_color)

    # Create the status text label
    status_text = tk.Label(root, text=" Maprova: PrinterA2", font=("Arial", 12, "bold"), bg="#79ff7d", fg="black")

    # Place the status dot and label together as a status bar
    status_dot.place(relx=0.0, rely=1.0, x=10, y=-17, anchor="sw")
    status_text.place(relx=0.0, rely=1.0, x=20, y=-10, anchor="sw")

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
