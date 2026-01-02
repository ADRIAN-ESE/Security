import sqlite3
import shutil
import os
from datetime import datetime, timedelta


def chrome_time_to_human(chrome_ticks):
    """Converts Chrome WebKit timestamp to a readable date."""
    if not chrome_ticks:
        return "N/A"
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_ticks)


def analyze_chrome_history():
    # Define the path to Chrome history (Standard Windows Path)
    # Note: You may need to change 'Default' to 'Profile 1' etc. depending on your setup.
    history_path = os.path.expanduser('~') + r"\AppData\Local\Google\Chrome\User Data\Default\History"

    # Forensic best practice: Copy the file first to avoid locking
    temp_history = "history_copy.db"
    try:
        shutil.copy2(history_path, temp_history)
        print(f"[+] Evidence acquired: {temp_history}")
    except Exception as e:
        print(f"[-] Could not find or copy history: {e}")
        return

    # Connect to the copied database
    conn = sqlite3.connect(temp_history)
    cursor = conn.cursor()

    try:
        # SQL Query to pull the data
        cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC")

        print(f"{'TITLE':<50} | {'VISIT COUNT':<12} | {'LAST VISIT'}")
        print("-" * 100)

        for row in cursor.fetchall()[:20]:  # Limit to top 20 for preview
            url, title, count, time_raw = row
            readable_time = chrome_time_to_human(time_raw)

            # Clean up long titles for display
            clean_title = (title[:47] + '...') if len(title) > 50 else title
            print(f"{clean_title:<50} | {count:<12} | {readable_time}")

    except sqlite3.Error as e:
        print(f"[-] SQL Error: {e}")
    finally:
        conn.close()
        # Clean up the copy after analysis
        # os.remove(temp_history)


if __name__ == "__main__":
    analyze_chrome_history()