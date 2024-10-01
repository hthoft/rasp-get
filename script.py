import os

# Path to the image you want to print
temp_image_path = "cog.png"

# Construct the print command
print_command = (
    "sudo BROTHER_QL_PRINTER=usb://0x04f9:0x2043 BROTHER_QL_MODEL=QL-710W "
    f"brother_ql print -l 62 {temp_image_path}"
)

# Execute the print command
os.system(print_command)
