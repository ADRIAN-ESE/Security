import asyncio
import socket
import ipaddress
import json
import csv
import time
from datetime import datetime

# --------------------------------------------
# Common Services
# --------------------------------------------
COMMON_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# --------------------------------------------
# Basic Vulnerability Signatures
# --------------------------------------------
VULN_SIGNATURES = {
    21: "FTP exposed (check anonymous login)",
    23: "Telnet exposed (insecure protocol)",
    445: "SMB exposed (possible EternalBlue risk)",
    3389: "RDP exposed (brute-force risk)",
    80: "HTTP exposed (check outdated web server)"
}


class MiniNmap:
    def __init__(self, target, start_port=1, end_port=1024, timeout=1):
        self.target_input = target
        self.start_port = start_port
        self.end_port = end_port
        self.timeout = timeout
        self.results = {}

    # --------------------------------------------
    # Resolve Host or Subnet
    # --------------------------------------------
    def parse_targets(self):
        targets = []

        try:
            # If CIDR subnet
            if "/" in self.target_input:
                network = ipaddress.ip_network(self.target_input, strict=False)
                for ip in network.hosts():
                    targets.append(str(ip))
            else:
                # Single host
                ip = socket.gethostbyname(self.target_input)
                targets.append(ip)
        except Exception:
            print("Invalid target.")
            exit()

        return targets

    # --------------------------------------------
    # Check if Host is Alive
    # --------------------------------------------
    async def is_host_alive(self, host):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 80),
                timeout=1
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    # --------------------------------------------
    # Scan Single Port
    # --------------------------------------------
    async def scan_port(self, host, port):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )

            service = COMMON_SERVICES.get(port, "Unknown")

            banner = ""
            try:
                writer.write(b"\r\n")
                await writer.drain()
                banner_data = await asyncio.wait_for(reader.read(1024), timeout=1)
                banner = banner_data.decode(errors="ignore").strip()
            except:
                banner = "No banner"

            vuln = VULN_SIGNATURES.get(port, "None")

            writer.close()
            await writer.wait_closed()

            return {
                "port": port,
                "service": service,
                "banner": banner,
                "vulnerability": vuln
            }

        except:
            return None

    # --------------------------------------------
    # Scan Host
    # --------------------------------------------
    async def scan_host(self, host):
        print(f"\n[*] Scanning Host: {host}")
        open_ports = []

        tasks = []
        for port in range(self.start_port, self.end_port + 1):
            tasks.append(self.scan_port(host, port))

        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                open_ports.append(result)
                print(f"[OPEN] {host}:{result['port']} | "
                      f"{result['service']} | "
                      f"{result['vulnerability']}")

        if open_ports:
            self.results[host] = open_ports

    # --------------------------------------------
    # Run Full Scan
    # --------------------------------------------
    async def run(self):
        start_time = time.time()
        targets = self.parse_targets()

        print("\n===== MINI NMAP ASYNC SCANNER =====")
        print(f"Targets: {len(targets)}")
        print(f"Port Range: {self.start_port}-{self.end_port}")
        print("====================================")

        # Host discovery phase
        alive_hosts = []
        print("\n[*] Discovering live hosts...")

        for host in targets:
            if await self.is_host_alive(host):
                print(f"[ALIVE] {host}")
                alive_hosts.append(host)

        # Scan alive hosts
        scan_tasks = [self.scan_host(host) for host in alive_hosts]
        await asyncio.gather(*scan_tasks)

        end_time = time.time()

        print("\nScan Complete.")
        print(f"Time Taken: {end_time - start_time:.2f} seconds")

        self.export_results()

    # --------------------------------------------
    # Export Results
    # --------------------------------------------
    def export_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON Export
        json_file = f"scan_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(self.results, f, indent=4)

        # CSV Export
        csv_file = f"scan_{timestamp}.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Host", "Port", "Service", "Banner", "Vulnerability"])

            for host, ports in self.results.items():
                for entry in ports:
                    writer.writerow([
                        host,
                        entry["port"],
                        entry["service"],
                        entry["banner"],
                        entry["vulnerability"]
                    ])

        print(f"\n[+] Results saved to {json_file} and {csv_file}")


# --------------------------------------------
# MAIN
# --------------------------------------------
if __name__ == "__main__":
    target = input("Enter target (IP, hostname, or subnet e.g. 192.168.1.0/24): ")
    start_port = int(input("Start port (default 1): ") or 1)
    end_port = int(input("End port (default 1024): ") or 1024)

    scanner = MiniNmap(target, start_port, end_port)
    asyncio.run(scanner.run())