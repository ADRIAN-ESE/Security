"""collectors.py — System info & geolocation data collectors."""

import platform, socket, uuid, os, datetime
from dataclasses import dataclass, field

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class SystemInfo:
    hostname: str = ""; os_name: str = ""; os_version: str = ""
    os_release: str = ""; architecture: str = ""; machine: str = ""
    processor: str = ""; python_version: str = ""; boot_time: str = ""
    current_user: str = ""; mac_address: str = ""

@dataclass
class CPUInfo:
    physical_cores: int = 0; logical_cores: int = 0
    max_freq_mhz: float = 0.0; current_freq_mhz: float = 0.0
    usage_percent: float = 0.0

@dataclass
class MemoryInfo:
    total_gb: float = 0.0; available_gb: float = 0.0
    used_gb: float = 0.0; percent_used: float = 0.0

@dataclass
class DiskPartition:
    device: str = ""; mountpoint: str = ""; fstype: str = ""
    total_gb: float = 0.0; used_gb: float = 0.0
    free_gb: float = 0.0; percent_used: float = 0.0

@dataclass
class NetworkInterface:
    name: str = ""; ip_addresses: list = field(default_factory=list)
    mac_address: str = ""; is_up: bool = False

@dataclass
class GeoLocation:
    public_ip: str = ""; country: str = ""; country_code: str = ""
    region: str = ""; city: str = ""; zip_code: str = ""
    latitude: float = 0.0; longitude: float = 0.0; timezone: str = ""
    isp: str = ""; org: str = ""; asn: str = ""
    is_proxy: bool = False; is_hosting: bool = False; error: str = ""

@dataclass
class FullReport:
    system: SystemInfo = field(default_factory=SystemInfo)
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disks: list = field(default_factory=list)
    interfaces: list = field(default_factory=list)
    geo: GeoLocation = field(default_factory=GeoLocation)
    generated_at: str = ""


# ── Collectors ───────────────────────────────────────────────────────────────

def collect_system() -> SystemInfo:
    s = SystemInfo()
    s.hostname       = socket.gethostname()
    s.os_name        = platform.system()
    s.os_version     = platform.version()
    s.os_release     = platform.release()
    s.architecture   = platform.architecture()[0]
    s.machine        = platform.machine()
    s.processor      = platform.processor() or "N/A"
    s.python_version = platform.python_version()
    s.mac_address    = ':'.join(f'{(uuid.getnode() >> i) & 0xff:02x}' for i in range(0, 48, 8)[::-1])
    try:
        s.current_user = os.getlogin()
    except Exception:
        s.current_user = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
    if HAS_PSUTIL:
        s.boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    return s


def collect_cpu() -> CPUInfo:
    c = CPUInfo()
    if not HAS_PSUTIL:
        return c
    c.physical_cores = psutil.cpu_count(logical=False) or 0
    c.logical_cores  = psutil.cpu_count(logical=True) or 0
    c.usage_percent  = psutil.cpu_percent(interval=0.3)
    freq = psutil.cpu_freq()
    if freq:
        c.max_freq_mhz     = round(freq.max, 1)
        c.current_freq_mhz = round(freq.current, 1)
    return c


def collect_memory() -> MemoryInfo:
    m = MemoryInfo()
    if not HAS_PSUTIL:
        return m
    vm = psutil.virtual_memory()
    m.total_gb     = round(vm.total     / 1024**3, 2)
    m.available_gb = round(vm.available / 1024**3, 2)
    m.used_gb      = round(vm.used      / 1024**3, 2)
    m.percent_used = vm.percent
    return m


def collect_disks() -> list:
    if not HAS_PSUTIL:
        return []
    result = []
    for p in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(p.mountpoint)
            result.append(DiskPartition(
                device=p.device, mountpoint=p.mountpoint, fstype=p.fstype,
                total_gb=round(u.total/1024**3,2), used_gb=round(u.used/1024**3,2),
                free_gb=round(u.free/1024**3,2),   percent_used=u.percent,
            ))
        except (PermissionError, OSError):
            continue
    return result


def collect_interfaces() -> list:
    if not HAS_PSUTIL:
        return []
    result = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, addr_list in addrs.items():
        iface = NetworkInterface(name=name, is_up=stats[name].isup if name in stats else False)
        for a in addr_list:
            if a.family == psutil.AF_LINK:
                iface.mac_address = a.address
            elif a.family in (socket.AF_INET, socket.AF_INET6):
                iface.ip_addresses.append(f"{a.address} ({a.family.name})")
        if iface.ip_addresses or iface.mac_address:
            result.append(iface)
    return result


def collect_geo() -> GeoLocation:
    g = GeoLocation()
    if not HAS_REQUESTS:
        g.error = "requests library not installed"
        return g
    try:
        r = requests.get(
            "http://ip-api.com/json/?fields=status,message,country,countryCode,"
            "region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting,query",
            timeout=6
        )
        d = r.json()
        if d.get("status") == "success":
            g.public_ip    = d.get("query", "")
            g.country      = d.get("country", "")
            g.country_code = d.get("countryCode", "")
            g.region       = d.get("regionName", "")
            g.city         = d.get("city", "")
            g.zip_code     = d.get("zip", "")
            g.latitude     = d.get("lat", 0.0)
            g.longitude    = d.get("lon", 0.0)
            g.timezone     = d.get("timezone", "")
            g.isp          = d.get("isp", "")
            g.org          = d.get("org", "")
            g.asn          = d.get("as", "")
            g.is_proxy     = d.get("proxy", False)
            g.is_hosting   = d.get("hosting", False)
        else:
            g.error = d.get("message", "Unknown error")
    except requests.exceptions.ConnectionError:
        g.error = "No internet connection"
    except Exception as e:
        g.error = str(e)
    return g


def build_report() -> FullReport:
    rpt = FullReport()
    rpt.generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rpt.system     = collect_system()
    rpt.cpu        = collect_cpu()
    rpt.memory     = collect_memory()
    rpt.disks      = collect_disks()
    rpt.interfaces = collect_interfaces()
    rpt.geo        = collect_geo()
    return rpt


def report_to_dict(report: FullReport) -> dict:
    """Recursively convert a FullReport to a plain dict."""
    def cvt(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: cvt(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [cvt(i) for i in obj]
        return obj
    return cvt(report)
