import sqlite3
import shutil
import os
from datetime import datetime, timedelta


def chrome_time_to_human(chrome_ticks):
    if not chrome_ticks: return "N/A"
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_ticks)


def keyword_search_history(keywords):
    history_path = os.path.expanduser('~') + r"\AppData\Local\Google\Chrome\User Data\Default\History"
    temp_history = "forensic_search.db"

    try:
        shutil.copy2(history_path, temp_history)
    except Exception as e:
        print(f"[-] Error accessing history: {e}")
        return

    conn = sqlite3.connect(temp_history)
    cursor = conn.cursor()

    print(f"\n[!] SCANNING FOR KEYWORDS: {keywords}")
    print("=" * 100)

    found_matches = 0
    for word in keywords:
        # The % symbol is a wildcard in SQL (matches any text before or after)
        query = "SELECT url, title, last_visit_time FROM urls WHERE url LIKE ? OR title LIKE ?"
        search_term = f"%{word}%"

        cursor.execute(query, (search_term, search_term))
        results = cursor.fetchall()

        for row in results:
            url, title, time_raw = row
            found_matches += 1
            print(f"[MATCH FOUND: '{word}']")
            print(f"Time:  {chrome_time_to_human(time_raw)}")
            print(f"Title: {title}")
            print(f"URL:   {url}\n" + "-" * 30)

    print(f"[*] Search complete. Total hits: {found_matches}")
    conn.close()


if __name__ == "__main__":
    # Add your own investigative keywords here
    target_keywords = ["crypto", "download", "login", "bank", "anonymous"]
    keyword_search_history(target_keywords)