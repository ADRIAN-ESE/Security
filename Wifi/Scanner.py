#!/usr/bin/env python3
import os
import platform
import subprocess
import re
import argparse
import json
from tabulate import tabulate

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

def main():
    parser = argparse.ArgumentParser(description="Cross-platform Wi-Fi Scanner")
    parser.add_argument("--json", help="Export results to JSON file")
    args = parser.parse_args()

    results = scan_wifi()

    # Sort by signal strength (descending)
    try:
        results.sort(key=lambda x: int(x.get("Signal","0")), reverse=True)
    except:
        pass

    # Pretty table
    headers = ["SSID", "BSSID", "Signal", "Security"]
    table = [[net.get("SSID"), net.get("BSSID"), net.get("Signal")+"%", net.get("Security")] for net in results]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

    # JSON Export
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=4)
        print(f"\n[+] Results exported to {args.json}")

if __name__ == "__main__":
    main()
