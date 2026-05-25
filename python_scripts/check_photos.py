"""Small script to check for corrupted image files in a directory.

Usage: python check_photos.py <directory>

To make it work in WSL from my Windows machine, you need to first map the
directory you want to scan to a WSL path.
Example: sudo mount -t drvfs 'Z:' /mnt/z
"""

import os
import sys
from PIL import Image

# Define which extensions to treat as photo files
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.sr2'
}


def is_image_file(filename):
    """Check if the file is an image based on its extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext in IMAGE_EXTENSIONS


def check_image_corruption(filepath):
    """Check if an image file is corrupted."""
    try:
        with Image.open(filepath) as img:
            img.verify()  # Verify that the image is not corrupted
        with Image.open(filepath) as img:
            img.load()  # Load the image to ensure it's fully readable
        return True
    except (IOError, SyntaxError):
        return False


def scan_directory_for_images(directory):
    """Scan the directory for image files and check for corruption."""
    corrupted_images = []
    total_files_scanned = 0

    if not os.path.isdir(directory):
        print(f"The path {directory} is not a valid directory.")
        sys.exit(1)

    for root, _, files in os.walk(directory):
        for filename in files:
            if is_image_file(filename):
                total_files_scanned += 1
                filepath = os.path.join(root, filename)
                print(f"Scanning file number: {total_files_scanned} - {filepath}")
                if not check_image_corruption(filepath):
                    print(f"Found corrupted image: {filepath}")
                    corrupted_images.append(filepath)

    return corrupted_images, total_files_scanned


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check for corrupted image files in a directory.")
    parser.add_argument("directory", type=str, help="The directory to scan for image files.")
    args = parser.parse_args()

    corrupted_files, total_files = scan_directory_for_images(args.directory)

    if corrupted_files:
        print(f"Total corrupted images found: {len(corrupted_files)}")
        for corrupted_file in corrupted_files:
            print(corrupted_file)
    else:
        print("No corrupted images found.")

    print(f"Total image files scanned: {total_files}")
    print("Scan completed.")
