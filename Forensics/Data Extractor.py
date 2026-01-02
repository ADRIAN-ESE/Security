import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from tkinter import filedialog, Tk


def get_geotagging(exif_data):
    """Decodes GPS coordinates into readable degrees/minutes/seconds."""
    if not exif_data:
        return None

    gps_info = {}
    for tag_id, value in exif_data.items():
        decoded = TAGS.get(tag_id, tag_id)
        if decoded == "GPSInfo":
            for t in value:
                sub_tag = GPSTAGS.get(t, t)
                gps_info[sub_tag] = value[t]

    return gps_info


def extract_metadata():
    # Hide the main Tkinter window
    root = Tk()
    root.withdraw()

    # Open a file selector
    file_path = filedialog.askopenfilename(title="Select Evidence Image",
                                           filetypes=[("Image files", "*.jpg *.jpeg *.tiff")])

    if not file_path:
        print("No file selected. Exiting...")
        return

    print(f"\n[+] Analyzing: {os.path.basename(file_path)}")

    try:
        img = Image.open(file_path)
        exif_data = img._getexif()

        if exif_data is None:
            print("[-] No EXIF metadata found. (It may have been stripped).")
            return

        # Print Standard Metadata
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name != "GPSInfo":  # Handle GPS separately
                print(f"{tag_name:25}: {value}")

        # Handle GPS Information
        gps_data = get_geotagging(exif_data)
        if gps_data:
            print("\n--- GPS LOCATION DATA FOUND ---")
            for key, val in gps_data.items():
                print(f"{key:25}: {val}")

            # Note: In a real tool, we'd convert these rational numbers to decimal
            print("\n[!] Use a site like 'latlong.net' to plot these coordinates.")

    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    extract_metadata()