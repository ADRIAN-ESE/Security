import socket
import threading
import csv
import time
import ipaddress
from queue import Queue

# ----------------------------------
# Common Port → Service Mapping
# ----------------------------------
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


# ----------------------------------
# Port Scanner Class
# ----------------------------------
class PortScanner:
    def __init__(self, target, start_port, end_port, threads=100, timeout=0.5):
        self.target = self.resolve_target(target)
        self.start_port = start_port
        self.end_port = end_port
        self.threads = threads
        self.timeout = timeout
        self.queue = Queue()
        self.lock = threading.Lock()
        self.open_ports = []
        self.total_ports = end_port - start_port + 1
        self.scanned_ports = 0

    # ----------------------------
    # Resolve hostname → IP
    # ----------------------------
    def resolve_target(self, target):
        try:
            # Check if valid IP
            ipaddress.ip_address(target)
            return target
        except ValueError:
            try:
                return socket.gethostbyname(target)
            except socket.gaierror:
                print("Invalid hostname or IP.")
                exit()

    # ----------------------------
    # Scan Single Port (TCP)
    # ----------------------------
    def scan_port(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                result = s.connect_ex((self.target, port))

                if result == 0:
                    banner = self.grab_banner(s)
                    service = COMMON_SERVICES.get(port, "Unknown")
                    with self.lock:
                        self.open_ports.append((port, service, banner))
                        print(f"[OPEN] Port {port} | {service} | {banner}")

        except Exception:
            pass
        finally:
            with self.lock:
                self.scanned_ports += 1
                self.print_progress()

    # ----------------------------
    # Banner Grabbing
    # ----------------------------
    def grab_banner(self, sock):
        try:
            sock.send(b"\r\n")
            return sock.recv(1024).decode(errors="ignore").strip()
        except:
            return "No banner"

    # ----------------------------
    # Worker Thread
    # ----------------------------
    def worker(self):
        while True:
            port = self.queue.get()
            if port is None:
                break
            self.scan_port(port)
            self.queue.task_done()

    # ----------------------------
    # Progress Display
    # ----------------------------
    def print_progress(self):
        percent = (self.scanned_ports / self.total_ports) * 100
        print(f"\rProgress: {percent:.2f}% ", end="")

    # ----------------------------
    # Run Scanner
    # ----------------------------
    def run(self):
        print(f"\n[*] Scanning {self.target}")
        print(f"[*] Ports: {self.start_port}-{self.end_port}")
        print(f"[*] Threads: {self.threads}\n")

        start_time = time.time()

        # Fill Queue
        for port in range(self.start_port, self.end_port + 1):
            self.queue.put(port)

        # Start Threads
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)

        # Wait for completion
        self.queue.join()

        # Stop threads
        for _ in threads:
            self.queue.put(None)
        for t in threads:
            t.join()

        end_time = time.time()

        print("\n\nScan Complete!")
        print(f"Open Ports Found: {len(self.open_ports)}")
        print(f"Time Taken: {end_time - start_time:.2f} seconds")

        self.export_results()

    # ----------------------------
    # Export Results
    # ----------------------------
    def export_results(self):
        filename = f"scan_results_{self.target}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Port", "Service", "Banner"])
            for port, service, banner in sorted(self.open_ports):
                writer.writerow([port, service, banner])

        print(f"[+] Results saved to {filename}")


# ----------------------------------
# Main
# ----------------------------------
if __name__ == "__main__":
    try:
        target = input("Target IP or hostname: ").strip()
        start_port = int(input("Start port: "))
        end_port = int(input("End port: "))
        threads = int(input("Threads (default 100): ") or 100)

        scanner = PortScanner(target, start_port, end_port, threads)
        scanner.run()

    except KeyboardInterrupt:
        print("\nScan interrupted by user.")