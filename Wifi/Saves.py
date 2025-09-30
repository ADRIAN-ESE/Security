#!/usr/bin/env python3
import os
import platform
import subprocess
import re
import argparse
import json
import time
from tabulate import tabulate

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def scan_wifi():
    system = platform.system().lower()

    if "windows" in system:
        return scan_windows()
    elif "darwin" in system:  # macOS
        return scan_macos()
    else:  # Linux fallback
        return scan_linux()

def scan_windows():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            shell=True, text=True, encoding="utf-8", errors="ignore"
        )
    except Exception as e:
        return [{"Error": str(e)}]

    networks = []
    current = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            if current:
                networks.append(current)
                current = {}
            ssid = line.split(":", 1)[1].strip()
            current["SSID"] = ssid if ssid else "Hidden Network"
        elif line.startswith("BSSID"):
            current["BSSID"] = line.split(":", 1)[1].strip()
        elif line.startswith("Signal"):
            current["Signal"] = line.split(":", 1)[1].strip().replace("%","")
        elif line.startswith("Authentication"):
            current["Security"] = line.split(":", 1)[1].strip()
    if current:
        networks.append(current)
    return networks

def scan_macos():
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    try:
        output = subprocess.check_output([airport, "-s"], text=True, encoding="utf-8", errors="ignore")
    except Exception as e:
        return [{"Error": str(e)}]

    networks = []
    for line in output.splitlines()[1:]:
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 3:
            networks.append({
                "SSID": parts[0] if parts[0] else "Hidden Network",
                "BSSID": parts[1],
                "Signal": parts[2].replace("%",""),
                "Security": parts[-1]
            })
    return networks

def scan_linux():
    try:
        output = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,SECURITY", "dev", "wifi"],
            text=True
        )
    except Exception as e:
        return [{"Error": str(e)}]

    networks = []
    for line in output.splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            networks.append({
                "SSID": parts[0] if parts[0] else "Hidden Network",
                "BSSID": parts[1],
                "Signal": parts[2],
                "Security": parts[3]
            })
    return networks

def signal_bar(signal_str):
    """Return a colored signal strength bar with %"""
    try:
        signal = int(signal_str)
    except:
        return signal_str

    if signal >= 70:
        color = GREEN
    elif signal >= 40:
        color = YELLOW
    else:
        color = RED

    length = max(1, min(10, signal // 10))
    bar = "█" * length + "-" * (10 - length)

    return f"{color}{bar}{RESET} {signal}%"

# ----------------- SAVED WIFI PROFILES ----------------- #
def saved_windows():
    profiles = {}
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "profiles"], text=True)
        for line in output.splitlines():
            if "All User Profile" in line:
                ssid = line.split(":", 1)[1].strip()
                try:
                    detail = subprocess.check_output(
                        ["netsh", "wlan", "show", "profile", ssid, "key=clear"], text=True
                    )
                    key = re.search(r"Key Content\s*:\s*(.*)", detail)
                    password = key.group(1).strip() if key else "(None)"
                except:
                    password = "(Error)"
                profiles[ssid] = password
    except Exception as e:
        profiles["Error"] = str(e)
    return profiles

def saved_macos():
    return {"Info": "Use: security find-generic-password -D 'AirPort network password' -a 'SSID' -gw (needs sudo)"}

def saved_linux():
    profiles = {}
    path = "/etc/NetworkManager/system-connections/"
    if os.path.isdir(path):
        for file in os.listdir(path):
            ssid = file
            try:
                with open(os.path.join(path, file), "r") as f:
                    data = f.read()
                pw_match = re.search(r"psk=([^\n]+)", data)
                password = pw_match.group(1) if pw_match else "(None)"
            except:
                password = "(Root required)"
            profiles[ssid] = password
    else:
        profiles["Error"] = "NetworkManager directory not accessible"
    return profiles

def get_saved_profiles():
    system = platform.system().lower()
    if "windows" in system:
        return saved_windows()
    elif "darwin" in system:
        return saved_macos()
    else:
        return saved_linux()

# ----------------- DISPLAY ----------------- #
def display_results(results, saved_profiles):
    try:
        results.sort(key=lambda x: int(x.get("Signal","0")), reverse=True)
    except:
        pass

    headers = ["SSID", "BSSID", "Signal", "Security", "Saved Password"]
    table = []
    for net in results:
        ssid = net.get("SSID")
        password = saved_profiles.get(ssid, "")
        table.append([ssid, net.get("BSSID"), signal_bar(net.get("Signal","0")), net.get("Security"), password])

    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# ----------------- MAIN ----------------- #
def main():
    parser = argparse.ArgumentParser(description="Cross-platform Wi-Fi Scanner")
    parser.add_argument("--json", help="Export results to JSON file")
    parser.add_argument("--live", type=int, help="Enable live scanning (refresh every X seconds)")
    args = parser.parse_args()

    saved_profiles = get_saved_profiles()

    if args.live:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                print(f"[+] Scanning Wi-Fi networks... (refresh every {args.live}s)\n")
                results = scan_wifi()
                display_results(results, saved_profiles)

                if args.json:
                    with open(args.json, "w") as f:
                        json.dump(results, f, indent=4)

                time.sleep(args.live)
        except KeyboardInterrupt:
            print("\n[!] Stopped live scanning.")
    else:
        results = scan_wifi()
        display_results(results, saved_profiles)

        if args.json:
            with open(args.json, "w") as f:
                json.dump(results, f, indent=4)
            print(f"\n[+] Results exported to {args.json}")

if __name__ == "__main__":
    main()

#83155789