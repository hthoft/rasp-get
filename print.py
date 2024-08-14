from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.backends import backend_factory
from brother_ql.raster import BrotherQLRaster
from PIL import Image

def handle_print():
    # Path to your image file
    image_path = "splash.png"  # Replace with your image path

    # Load the image using PIL
    image = Image.open(image_path)

    # Resize the image with LANCZOS filter if needed
    new_width, new_height = 696, 1122  # Adjust these dimensions as necessary for your label
    image = image.resize((new_width, new_height), resample=Image.LANCZOS)

    # Set up the Brother QL-710W printer using USB
    usb_path = 'usb://0x04f9:0x2042'  # Adjust this USB path if needed
    qlr = BrotherQLRaster('QL-710W')
    qlr.exception_on_warning = True

    # Convert the image to the printer's format
    instructions = convert(
        qlr=qlr,
        images=[image],  # Pass the PIL image here
        label="62",  # 62mm continuous roll, adjust if you use a different label
        rotate="90",  # Rotate the image to fit the label orientation
        threshold=70.0,
        cut=True
    )

    # Prepare the backend for USB
    backend = backend_factory('pyusb')

    # Send the print job to the printer
    try:
        send(instructions=instructions, printer_identifier=usb_path, backend_identifier=backend)
        print("Printing job sent successfully")
    except Exception as e:
        print(f"Failed to print: {e}")

# Call the function to handle the print job
handle_print()
