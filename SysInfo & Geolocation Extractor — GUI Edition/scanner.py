"""scanner.py — Ping sweep & port scanner."""

import socket
import platform
import subprocess
import concurrent.futures
import ipaddress
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


COMMON_PORTS = {
    21: "FTP",   22: "SSH",    23: "Telnet",  25: "SMTP",
    53: "DNS",   80: "HTTP",   110: "POP3",   135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    3306: "MySQL", 3389: "RDP",  5432: "PostgreSQL",
    5900: "VNC",  6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
    27017: "MongoDB",
}


@dataclass
class ScanHost:
    ip: str = ""
    hostname: str = ""
    is_alive: bool = False
    response_ms: float = 0.0
    open_ports: list = field(default_factory=list)  # list of (port, service)


def _ping_once(ip: str) -> tuple[bool, float]:
    """Return (is_alive, response_time_ms)."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        t0 = time.monotonic()
        result = subprocess.run(
            ["ping", param, "1", timeout_flag, "1", str(ip)],
            capture_output=True, text=True, timeout=3
        )
        ms = round((time.monotonic() - t0) * 1000, 1)
        return result.returncode == 0, ms
    except Exception:
        return False, 0.0


def _resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(str(ip))[0]
    except Exception:
        return ""


def ping_sweep(
    subnet: str,
    max_workers: int = 50,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
    stop_flag: Optional[list] = None,
) -> list[ScanHost]:
    """
    Ping all hosts in a subnet (e.g. '192.168.1.0/24').
    progress_cb(done, total, current_ip) called after each host.
    stop_flag: a list; set stop_flag[0]=True to abort.
    """
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        raise ValueError(f"Invalid subnet: {e}")

    hosts = list(network.hosts())
    total = len(hosts)
    results: list[ScanHost] = []

    def _scan_one(ip):
        alive, ms = _ping_once(str(ip))
        host = ScanHost(ip=str(ip), is_alive=alive, response_ms=ms)
        if alive:
            host.hostname = _resolve_hostname(str(ip))
        return host

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_scan_one, ip): ip for ip in hosts}
        for future in concurrent.futures.as_completed(futures):
            if stop_flag and stop_flag[0]:
                ex.shutdown(wait=False, cancel_futures=True)
                break
            host = future.result()
            results.append(host)
            done += 1
            if progress_cb:
                progress_cb(done, total, host.ip)

    return sorted(results, key=lambda h: ipaddress.ip_address(h.ip))


def scan_ports(
    ip: str,
    ports: Optional[list[int]] = None,
    timeout: float = 0.5,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    stop_flag: Optional[list] = None,
) -> list[tuple[int, str]]:
    """
    Scan ports on a single IP. Returns list of (port, service_name) tuples.
    """
    if ports is None:
        ports = list(COMMON_PORTS.keys())

    open_ports = []
    total = len(ports)

    def _check(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            res = s.connect_ex((str(ip), port))
            s.close()
            return port, res == 0
        except Exception:
            return port, False

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        futures = {ex.submit(_check, p): p for p in ports}
        for future in concurrent.futures.as_completed(futures):
            if stop_flag and stop_flag[0]:
                ex.shutdown(wait=False, cancel_futures=True)
                break
            port, is_open = future.result()
            done += 1
            if is_open:
                service = COMMON_PORTS.get(port, "unknown")
                open_ports.append((port, service))
            if progress_cb:
                progress_cb(done, total, port)

    return sorted(open_ports, key=lambda x: x[0])


def get_local_subnet() -> str:
    """Best-guess at the local /24 subnet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.rsplit(".", 1)
        return f"{parts[0]}.0/24"
    except Exception:
        return "192.168.1.0/24"
