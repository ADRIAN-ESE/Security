import hashlib
import os
import time
import json
import stat
from datetime import datetime

# ================= CONFIG =================
MONITOR_DIR = "./target_files"
BASELINE_FILE = "baseline.json"
LOG_FILE = "fim.log"
SCAN_INTERVAL = 2  # seconds
# ==========================================


def log_event(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as log:
        log.write(entry + "\n")


def calculate_hash(filepath):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


def get_file_metadata(filepath):
    try:
        stats = os.stat(filepath)
        return {
            "size": stats.st_size,
            "mtime": stats.st_mtime,
            "permissions": stat.filemode(stats.st_mode),
            "hash": calculate_hash(filepath)
        }
    except Exception:
        return None


# ================= BASELINE =================
def create_baseline():
    baseline = {}
    log_event("INFO", f"Creating baseline for {MONITOR_DIR}")

    for root, _, files in os.walk(MONITOR_DIR):
        for file in files:
            path = os.path.join(root, file)
            metadata = get_file_metadata(path)
            if metadata:
                baseline[path] = metadata

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)

    log_event("INFO", f"Baseline created with {len(baseline)} files")


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return {}

    with open(BASELINE_FILE, "r") as f:
        return json.load(f)


# ================= MONITOR =================
def monitor():
    log_event("INFO", "Starting File Integrity Monitoring")
    baseline = load_baseline()

    while True:
        time.sleep(SCAN_INTERVAL)

        current_files = {}

        # Scan current state
        for root, _, files in os.walk(MONITOR_DIR):
            for file in files:
                path = os.path.join(root, file)
                metadata = get_file_metadata(path)
                if metadata:
                    current_files[path] = metadata

                    if path not in baseline:
                        log_event("CRITICAL", f"NEW FILE: {path}")
                        baseline[path] = metadata
                        continue

                    # Metadata comparison
                    base_meta = baseline[path]
                    if metadata["size"] != base_meta["size"] or metadata["mtime"] != base_meta["mtime"]:
                        if metadata["hash"] != base_meta["hash"]:
                            log_event("CRITICAL", f"MODIFIED FILE: {path}")
                        baseline[path] = metadata

        # Detect deletions
        for path in list(baseline.keys()):
            if path not in current_files:
                log_event("CRITICAL", f"DELETED FILE: {path}")
                del baseline[path]


# ================= MAIN =================
if __name__ == "__main__":
    choice = input("(A) Create Baseline  (B) Start Monitoring: ").upper()

    if choice == "A":
        create_baseline()
    elif choice == "B":
        if not os.path.exists(BASELINE_FILE):
            log_event("ERROR", "Baseline missing. Create one first.")
        else:
            monitor()
    else:
        print("Invalid choice.")
