"""
============================================================
  System Info & Geolocation Extractor
  Cybersecurity Recon Tool | Python 3.10+
============================================================
  Collects: OS, CPU, RAM, Disk, Network Interfaces,
            Public IP, and Geolocation Data
============================================================
"""

import platform
import socket
import uuid
import os
import json
import datetime
import ipaddress
from dataclasses import dataclass, field
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import requests
except ImportError:
    requests = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


console = Console() if HAS_RICH else None

# ─────────────────────────────────────────────
#  Data Classes
# ─────────────────────────────────────────────

@dataclass
class SystemInfo:
    hostname: str = ""
    os_name: str = ""
    os_version: str = ""
    os_release: str = ""
    architecture: str = ""
    machine: str = ""
    processor: str = ""
    python_version: str = ""
    boot_time: str = ""
    current_user: str = ""
    mac_address: str = ""

@dataclass
class CPUInfo:
    physical_cores: int = 0
    logical_cores: int = 0
    max_frequency_mhz: float = 0.0
    current_frequency_mhz: float = 0.0
    cpu_usage_percent: float = 0.0

@dataclass
class MemoryInfo:
    total_gb: float = 0.0
    available_gb: float = 0.0
    used_gb: float = 0.0
    percent_used: float = 0.0

@dataclass
class DiskPartition:
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    percent_used: float = 0.0

@dataclass
class NetworkInterface:
    name: str = ""
    ip_addresses: list = field(default_factory=list)
    mac_address: str = ""
    is_up: bool = False

@dataclass
class GeoLocation:
    public_ip: str = ""
    country: str = ""
    country_code: str = ""
    region: str = ""
    city: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = ""
    isp: str = ""
    org: str = ""
    asn: str = ""
    is_proxy: bool = False
    is_hosting: bool = False

@dataclass
class FullReport:
    system: SystemInfo = field(default_factory=SystemInfo)
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disks: list = field(default_factory=list)
    interfaces: list = field(default_factory=list)
    geo: GeoLocation = field(default_factory=GeoLocation)
    generated_at: str = ""


# ─────────────────────────────────────────────
#  Collectors
# ─────────────────────────────────────────────

def collect_system_info() -> SystemInfo:
    info = SystemInfo()
    info.hostname        = socket.gethostname()
    info.os_name         = platform.system()
    info.os_version      = platform.version()
    info.os_release      = platform.release()
    info.architecture    = platform.architecture()[0]
    info.machine         = platform.machine()
    info.processor       = platform.processor() or "N/A"
    info.python_version  = platform.python_version()
    info.current_user    = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get("USER", "unknown")
    info.mac_address     = ':'.join(f'{(uuid.getnode() >> i) & 0xff:02x}' for i in range(0, 48, 8)[::-1])

    if psutil:
        bt = datetime.datetime.fromtimestamp(psutil.boot_time())
        info.boot_time = bt.strftime("%Y-%m-%d %H:%M:%S")

    return info


def collect_cpu_info() -> CPUInfo:
    cpu = CPUInfo()
    if not psutil:
        return cpu

    cpu.physical_cores = psutil.cpu_count(logical=False) or 0
    cpu.logical_cores  = psutil.cpu_count(logical=True) or 0
    cpu.cpu_usage_percent = psutil.cpu_percent(interval=0.5)

    freq = psutil.cpu_freq()
    if freq:
        cpu.max_frequency_mhz     = round(freq.max, 2)
        cpu.current_frequency_mhz = round(freq.current, 2)

    return cpu


def collect_memory_info() -> MemoryInfo:
    mem = MemoryInfo()
    if not psutil:
        return mem

    vm = psutil.virtual_memory()
    mem.total_gb     = round(vm.total / (1024 ** 3), 2)
    mem.available_gb = round(vm.available / (1024 ** 3), 2)
    mem.used_gb      = round(vm.used / (1024 ** 3), 2)
    mem.percent_used = vm.percent

    return mem


def collect_disk_info() -> list[DiskPartition]:
    partitions = []
    if not psutil:
        return partitions

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            dp = DiskPartition(
                device      = part.device,
                mountpoint  = part.mountpoint,
                fstype      = part.fstype,
                total_gb    = round(usage.total / (1024 ** 3), 2),
                used_gb     = round(usage.used  / (1024 ** 3), 2),
                free_gb     = round(usage.free  / (1024 ** 3), 2),
                percent_used= usage.percent,
            )
            partitions.append(dp)
        except (PermissionError, OSError):
            continue

    return partitions


def collect_network_interfaces() -> list[NetworkInterface]:
    interfaces = []
    if not psutil:
        return interfaces

    addrs   = psutil.net_if_addrs()
    stats   = psutil.net_if_stats()

    for name, addr_list in addrs.items():
        iface = NetworkInterface(name=name)
        iface.is_up = stats[name].isup if name in stats else False

        for addr in addr_list:
            # MAC
            if addr.family == psutil.AF_LINK:
                iface.mac_address = addr.address
            # IPv4 / IPv6
            elif addr.family in (socket.AF_INET, socket.AF_INET6):
                iface.ip_addresses.append(f"{addr.address} ({addr.family.name})")

        if iface.ip_addresses or iface.mac_address:
            interfaces.append(iface)

    return interfaces


def collect_geolocation() -> GeoLocation:
    geo = GeoLocation()
    if not requests:
        geo.public_ip = "requests library not installed"
        return geo

    try:
        # Use ip-api.com (free, no key required)
        response = requests.get(
            "http://ip-api.com/json/?fields=status,message,country,countryCode,"
            "region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting,query",
            timeout=5
        )
        data = response.json()

        if data.get("status") == "success":
            geo.public_ip    = data.get("query", "")
            geo.country      = data.get("country", "")
            geo.country_code = data.get("countryCode", "")
            geo.region       = data.get("regionName", "")
            geo.city         = data.get("city", "")
            geo.zip_code     = data.get("zip", "")
            geo.latitude     = data.get("lat", 0.0)
            geo.longitude    = data.get("lon", 0.0)
            geo.timezone     = data.get("timezone", "")
            geo.isp          = data.get("isp", "")
            geo.org          = data.get("org", "")
            geo.asn          = data.get("as", "")
            geo.is_proxy     = data.get("proxy", False)
            geo.is_hosting   = data.get("hosting", False)
        else:
            geo.public_ip = f"Error: {data.get('message', 'unknown')}"

    except requests.exceptions.ConnectionError:
        geo.public_ip = "No internet connection"
    except Exception as e:
        geo.public_ip = f"Error: {str(e)}"

    return geo


# ─────────────────────────────────────────────
#  Report Builder
# ─────────────────────────────────────────────

def build_report() -> FullReport:
    report = FullReport()
    report.generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if HAS_RICH:
        console.print("\n[bold cyan]⚙  Collecting system information...[/bold cyan]")

    report.system     = collect_system_info()
    report.cpu        = collect_cpu_info()
    report.memory     = collect_memory_info()
    report.disks      = collect_disk_info()
    report.interfaces = collect_network_interfaces()

    if HAS_RICH:
        console.print("[bold cyan]🌐  Fetching geolocation data...[/bold cyan]")

    report.geo = collect_geolocation()
    return report


# ─────────────────────────────────────────────
#  Display (Rich)
# ─────────────────────────────────────────────

def display_report_rich(report: FullReport):
    console.print()
    console.rule("[bold green]  SYSTEM INFO & GEOLOCATION EXTRACTOR  ")
    console.print(f"[dim]  Report generated: {report.generated_at}[/dim]\n")

    # ── System ──────────────────────────────
    sys_table = Table(box=box.ROUNDED, show_header=False, pad_edge=True, border_style="cyan")
    sys_table.add_column("Field", style="bold green", width=22)
    sys_table.add_column("Value", style="white")

    s = report.system
    sys_table.add_row("Hostname",       s.hostname)
    sys_table.add_row("OS",             f"{s.os_name} {s.os_release}")
    sys_table.add_row("OS Version",     s.os_version[:60] + "..." if len(s.os_version) > 60 else s.os_version)
    sys_table.add_row("Architecture",   f"{s.architecture} / {s.machine}")
    sys_table.add_row("Processor",      s.processor[:60] if s.processor else "N/A")
    sys_table.add_row("Python Version", s.python_version)
    sys_table.add_row("Current User",   s.current_user)
    sys_table.add_row("MAC Address",    s.mac_address)
    sys_table.add_row("Boot Time",      s.boot_time)

    console.print(Panel(sys_table, title="[bold cyan]🖥  System[/bold cyan]", border_style="cyan"))

    # ── CPU ─────────────────────────────────
    cpu = report.cpu
    cpu_table = Table(box=box.ROUNDED, show_header=False, pad_edge=True, border_style="yellow")
    cpu_table.add_column("Field", style="bold yellow", width=22)
    cpu_table.add_column("Value", style="white")
    cpu_table.add_row("Physical Cores",    str(cpu.physical_cores))
    cpu_table.add_row("Logical Cores",     str(cpu.logical_cores))
    cpu_table.add_row("Max Frequency",     f"{cpu.max_frequency_mhz} MHz")
    cpu_table.add_row("Current Frequency", f"{cpu.current_frequency_mhz} MHz")
    cpu_table.add_row("CPU Usage",         f"{cpu.cpu_usage_percent}%")

    # ── Memory ──────────────────────────────
    mem = report.memory
    mem_table = Table(box=box.ROUNDED, show_header=False, pad_edge=True, border_style="magenta")
    mem_table.add_column("Field", style="bold magenta", width=22)
    mem_table.add_column("Value", style="white")
    mem_table.add_row("Total RAM",     f"{mem.total_gb} GB")
    mem_table.add_row("Used RAM",      f"{mem.used_gb} GB")
    mem_table.add_row("Available RAM", f"{mem.available_gb} GB")
    mem_table.add_row("Usage",         f"{mem.percent_used}%")

    console.print(Columns([
        Panel(cpu_table,  title="[bold yellow]⚡  CPU[/bold yellow]",    border_style="yellow"),
        Panel(mem_table,  title="[bold magenta]💾  Memory[/bold magenta]", border_style="magenta"),
    ]))

    # ── Disks ───────────────────────────────
    disk_table = Table(box=box.ROUNDED, pad_edge=True, border_style="blue")
    disk_table.add_column("Device",     style="bold blue")
    disk_table.add_column("Mount",      style="white")
    disk_table.add_column("FS Type",    style="dim")
    disk_table.add_column("Total (GB)", style="cyan",   justify="right")
    disk_table.add_column("Used (GB)",  style="yellow", justify="right")
    disk_table.add_column("Free (GB)",  style="green",  justify="right")
    disk_table.add_column("Usage %",    style="red",    justify="right")

    for d in report.disks:
        disk_table.add_row(
            d.device, d.mountpoint, d.fstype,
            str(d.total_gb), str(d.used_gb), str(d.free_gb), f"{d.percent_used}%"
        )

    console.print(Panel(disk_table, title="[bold blue]💿  Disk Partitions[/bold blue]", border_style="blue"))

    # ── Network Interfaces ──────────────────
    net_table = Table(box=box.ROUNDED, pad_edge=True, border_style="green")
    net_table.add_column("Interface", style="bold green")
    net_table.add_column("Status",    style="white", justify="center")
    net_table.add_column("MAC",       style="dim")
    net_table.add_column("IP Addresses", style="cyan")

    for iface in report.interfaces:
        status = "[bold green]UP[/bold green]" if iface.is_up else "[bold red]DOWN[/bold red]"
        net_table.add_row(
            iface.name,
            status,
            iface.mac_address or "—",
            "\n".join(iface.ip_addresses) or "—"
        )

    console.print(Panel(net_table, title="[bold green]🔌  Network Interfaces[/bold green]", border_style="green"))

    # ── Geolocation ─────────────────────────
    geo = report.geo
    geo_table = Table(box=box.ROUNDED, show_header=False, pad_edge=True, border_style="red")
    geo_table.add_column("Field", style="bold red", width=22)
    geo_table.add_column("Value", style="white")

    geo_table.add_row("Public IP",    geo.public_ip)
    geo_table.add_row("Country",      f"{geo.country} ({geo.country_code})")
    geo_table.add_row("Region",       geo.region)
    geo_table.add_row("City",         geo.city)
    geo_table.add_row("ZIP Code",     geo.zip_code)
    geo_table.add_row("Coordinates",  f"Lat {geo.latitude}, Lon {geo.longitude}")
    geo_table.add_row("Timezone",     geo.timezone)
    geo_table.add_row("ISP",          geo.isp)
    geo_table.add_row("Organization", geo.org)
    geo_table.add_row("ASN",          geo.asn)
    geo_table.add_row("Proxy/VPN",    "[bold red]YES[/bold red]" if geo.is_proxy else "[green]No[/green]")
    geo_table.add_row("Hosting/DC",   "[bold red]YES[/bold red]" if geo.is_hosting else "[green]No[/green]")

    console.print(Panel(geo_table, title="[bold red]🌍  Geolocation (Public IP)[/bold red]", border_style="red"))
    console.rule("[dim]End of Report[/dim]")
    console.print()


# ─────────────────────────────────────────────
#  Display (Plain Fallback)
# ─────────────────────────────────────────────

def display_report_plain(report: FullReport):
    def section(title):
        print(f"\n{'='*50}")
        print(f"  {title}")
        print('='*50)

    def row(label, value):
        print(f"  {label:<22} {value}")

    print("\n" + "="*50)
    print("  SYSTEM INFO & GEOLOCATION EXTRACTOR")
    print(f"  Generated: {report.generated_at}")
    print("="*50)

    section("SYSTEM")
    s = report.system
    row("Hostname:",      s.hostname)
    row("OS:",            f"{s.os_name} {s.os_release}")
    row("Architecture:",  f"{s.architecture} / {s.machine}")
    row("Processor:",     s.processor)
    row("Python:",        s.python_version)
    row("User:",          s.current_user)
    row("MAC Address:",   s.mac_address)
    row("Boot Time:",     s.boot_time)

    section("CPU")
    c = report.cpu
    row("Physical Cores:",    str(c.physical_cores))
    row("Logical Cores:",     str(c.logical_cores))
    row("Max Freq (MHz):",    str(c.max_frequency_mhz))
    row("Usage:",             f"{c.cpu_usage_percent}%")

    section("MEMORY")
    m = report.memory
    row("Total:",     f"{m.total_gb} GB")
    row("Used:",      f"{m.used_gb} GB")
    row("Available:", f"{m.available_gb} GB")
    row("Usage:",     f"{m.percent_used}%")

    section("DISKS")
    for d in report.disks:
        print(f"\n  [{d.device}] → {d.mountpoint} ({d.fstype})")
        row("  Total:",  f"{d.total_gb} GB")
        row("  Used:",   f"{d.used_gb} GB")
        row("  Free:",   f"{d.free_gb} GB")
        row("  Usage:",  f"{d.percent_used}%")

    section("NETWORK INTERFACES")
    for iface in report.interfaces:
        status = "UP" if iface.is_up else "DOWN"
        print(f"\n  [{iface.name}] — {status}")
        row("  MAC:", iface.mac_address or "—")
        for ip in iface.ip_addresses:
            row("  IP:", ip)

    section("GEOLOCATION")
    g = report.geo
    row("Public IP:",    g.public_ip)
    row("Country:",      f"{g.country} ({g.country_code})")
    row("Region:",       g.region)
    row("City:",         g.city)
    row("Coordinates:",  f"Lat {g.latitude}, Lon {g.longitude}")
    row("Timezone:",     g.timezone)
    row("ISP:",          g.isp)
    row("ASN:",          g.asn)
    row("Proxy/VPN:",    "YES" if g.is_proxy else "No")
    row("Hosting/DC:",   "YES" if g.is_hosting else "No")

    print("\n" + "="*50 + "\n")


# ─────────────────────────────────────────────
#  JSON Export
# ─────────────────────────────────────────────

def export_json(report: FullReport, filepath: str = "system_report.json"):
    def to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [to_dict(i) for i in obj]
        return obj

    data = to_dict(report)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    if HAS_RICH:
        console.print(f"[bold green]✅  Report saved to:[/bold green] [cyan]{filepath}[/cyan]\n")
    else:
        print(f"\n  Report saved to: {filepath}\n")


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    report = build_report()

    if HAS_RICH:
        display_report_rich(report)
    else:
        display_report_plain(report)

    # Uncomment to save JSON report:
    # export_json(report)
