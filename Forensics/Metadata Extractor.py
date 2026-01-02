import os
import csv
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from tkinter import filedialog, Tk


def extract_metadata():
    root = Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Select Evidence Image")

    if not file_path:
        return

    report_name = f"Forensic_Report_{os.path.basename(file_path)}.csv"

    try:
        img = Image.open(file_path)
        exif_data = img._getexif()

        # Create/Open the CSV file
        with open(report_name, mode='w', newline='', encoding='utf-8') as report_file:
            writer = csv.writer(report_file)
            # Write Header
            writer.writerow(["Artifact Name", "Value", "Extraction Timestamp"])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    # Special handling for GPS to keep it in one cell
                    if tag_name == "GPSInfo":
                        gps_info = {}
                        for t in value:
                            sub_tag = GPSTAGS.get(t, t)
                            gps_info[sub_tag] = value[t]
                        writer.writerow([tag_name, str(gps_info), timestamp])
                    else:
                        writer.writerow([tag_name, str(value), timestamp])

                print(f"[+] Forensic Report generated: {report_name}")
            else:
                print("[-] No metadata found to write.")

    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    extract_metadata()