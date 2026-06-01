#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║        CyberSec DNS Lookup Toolkit           ║
║   DNS Reconnaissance for Security Analysts  ║
╚══════════════════════════════════════════════╝

Features:
  - Full DNS record enumeration (A, AAAA, MX, NS, TXT, CNAME, SOA)
  - Reverse DNS lookup
  - WHOIS domain intelligence
  - IP Geolocation
  - Zone Transfer vulnerability check
  - Common subdomain brute-force
  - VirusTotal threat intel (optional API key)
  - Export results to JSON
"""

import dns.resolver
import dns.reversename
import dns.zone
import dns.query
import dns.exception
import socket
import requests
import json
import sys
import argparse
import time
import re
from datetime import datetime

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    C_RED     = Fore.RED
    C_GREEN   = Fore.GREEN
    C_YELLOW  = Fore.YELLOW
    C_CYAN    = Fore.CYAN
    C_BLUE    = Fore.BLUE
    C_MAGENTA = Fore.MAGENTA
    C_WHITE   = Fore.WHITE
    C_RESET   = Style.RESET_ALL
    C_BOLD    = Style.BRIGHT
except ImportError:
    C_RED = C_GREEN = C_YELLOW = C_CYAN = C_BLUE = C_MAGENTA = C_WHITE = C_RESET = C_BOLD = ""

# ─── Common subdomains for brute-force ────────────────────────────────────────
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "remote",
    "vpn", "api", "dev", "staging", "test", "beta", "admin", "portal",
    "login", "secure", "ns1", "ns2", "mx", "blog", "shop", "store",
    "static", "cdn", "media", "images", "assets", "dashboard", "app",
    "m", "mobile", "wap", "help", "support", "docs", "wiki", "status",
    "monitor", "health", "git", "gitlab", "jenkins", "ci", "jira",
    "confluence", "intranet", "internal", "corp", "old", "legacy",
    "backup", "db", "database", "mysql", "redis", "es", "elastic",
    "auth", "sso", "oauth", "id", "identity", "exchange", "owa",
    "autodiscover", "lyncdiscover", "meet", "voice", "video",
]

# ─── DNS Record Types ─────────────────────────────────────────────────────────
DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA", "SRV"]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{C_CYAN}{C_BOLD}
  ██████╗ ███╗   ██╗███████╗    ██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗
  ██╔══██╗████╗  ██║██╔════╝    ██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
  ██║  ██║██╔██╗ ██║███████╗    ██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
  ██║  ██║██║╚██╗██║╚════██║    ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝
  ██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║
  ╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝
{C_RESET}{C_YELLOW}                  CyberSec DNS Recon Toolkit  |  v1.0
{C_RESET}""")

def section(title):
    width = 60
    print(f"\n{C_CYAN}{C_BOLD}{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}{C_RESET}")

def ok(msg):    print(f"  {C_GREEN}[+]{C_RESET} {msg}")
def warn(msg):  print(f"  {C_YELLOW}[!]{C_RESET} {msg}")
def err(msg):   print(f"  {C_RED}[-]{C_RESET} {msg}")
def info(msg):  print(f"  {C_BLUE}[*]{C_RESET} {msg}")

def is_ip(target):
    try:
        socket.inet_aton(target)
        return True
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, target)
            return True
        except OSError:
            return False

def sanitize(target):
    target = target.strip().lower()
    target = re.sub(r'^https?://', '', target)
    target = target.split('/')[0]
    return target

# ─── DNS Record Lookups ───────────────────────────────────────────────────────

def query_records(domain, record_type, resolver=None):
    """Return list of (record_type, value) tuples or empty list on failure."""
    try:
        res = resolver or dns.resolver.Resolver()
        answers = res.resolve(domain, record_type, lifetime=5)
        results = []
        for rdata in answers:
            results.append(str(rdata))
        return results
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout,
            dns.resolver.NoNameservers):
        return []
    except Exception:
        return []

def dns_enum(domain, results_dict):
    section("📋  DNS Record Enumeration")
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5

    found_any = False
    for rtype in DNS_RECORD_TYPES:
        records = query_records(domain, rtype, resolver)
        if records:
            found_any = True
            results_dict.setdefault("dns_records", {})[rtype] = records
            print(f"\n  {C_MAGENTA}{C_BOLD}{rtype} Records:{C_RESET}")
            for r in records:
                ok(r)

    if not found_any:
        err("No DNS records found.")

# ─── Reverse DNS ──────────────────────────────────────────────────────────────

def reverse_dns(ip, results_dict):
    section("🔄  Reverse DNS Lookup")
    try:
        rev_name = dns.reversename.from_address(ip)
        answers = dns.resolver.resolve(rev_name, "PTR", lifetime=5)
        hostnames = [str(a) for a in answers]
        ok(f"IP {C_YELLOW}{ip}{C_RESET} → {C_GREEN}{', '.join(hostnames)}{C_RESET}")
        results_dict["reverse_dns"] = hostnames
    except Exception as e:
        err(f"No PTR record found for {ip}: {e}")
        results_dict["reverse_dns"] = []

# ─── IP Geolocation ───────────────────────────────────────────────────────────

def geolocate(ip, results_dict):
    section("🌍  IP Geolocation")
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,reverse,mobile,proxy,hosting", timeout=5)
        data = resp.json()
        if data.get("status") == "success":
            geo = {
                "ip":       ip,
                "country":  data.get("country", "N/A"),
                "region":   data.get("regionName", "N/A"),
                "city":     data.get("city", "N/A"),
                "zip":      data.get("zip", "N/A"),
                "lat":      data.get("lat"),
                "lon":      data.get("lon"),
                "timezone": data.get("timezone", "N/A"),
                "isp":      data.get("isp", "N/A"),
                "org":      data.get("org", "N/A"),
                "asn":      data.get("as", "N/A"),
                "reverse":  data.get("reverse", "N/A"),
                "is_mobile":  data.get("mobile", False),
                "is_proxy":   data.get("proxy", False),
                "is_hosting": data.get("hosting", False),
            }
            results_dict["geolocation"] = geo

            ok(f"Country  : {C_YELLOW}{geo['country']}{C_RESET}")
            ok(f"Region   : {geo['region']}, {geo['city']} {geo['zip']}")
            ok(f"Coords   : {geo['lat']}, {geo['lon']}  (TZ: {geo['timezone']})")
            ok(f"ISP/Org  : {geo['isp']} / {geo['org']}")
            ok(f"ASN      : {geo['asn']}")

            flags = []
            if geo["is_proxy"]:   flags.append(f"{C_RED}PROXY{C_RESET}")
            if geo["is_hosting"]: flags.append(f"{C_YELLOW}HOSTING/VPS{C_RESET}")
            if geo["is_mobile"]:  flags.append("MOBILE")
            if flags:
                warn(f"Flags    : {' | '.join(flags)}")
        else:
            err(f"Geolocation failed: {data.get('message', 'unknown error')}")
    except Exception as e:
        err(f"Geolocation request failed: {e}")

# ─── WHOIS ────────────────────────────────────────────────────────────────────

def whois_lookup(domain, results_dict):
    section("📄  WHOIS Intelligence")
    if not WHOIS_AVAILABLE:
        warn("python-whois not installed. Skipping WHOIS.")
        return
    try:
        w = whois.whois(domain)
        data = {
            "registrar":       str(w.registrar or "N/A"),
            "creation_date":   str(w.creation_date) if w.creation_date else "N/A",
            "expiration_date": str(w.expiration_date) if w.expiration_date else "N/A",
            "updated_date":    str(w.updated_date) if w.updated_date else "N/A",
            "name_servers":    [str(ns).lower() for ns in (w.name_servers or [])],
            "status":          str(w.status or "N/A"),
            "emails":          list(set(w.emails)) if w.emails else [],
            "country":         str(w.country or "N/A"),
            "org":             str(w.org or "N/A"),
        }
        results_dict["whois"] = data

        ok(f"Registrar      : {C_YELLOW}{data['registrar']}{C_RESET}")
        ok(f"Created        : {data['creation_date']}")
        ok(f"Expires        : {data['expiration_date']}")
        ok(f"Last Updated   : {data['updated_date']}")
        ok(f"Org / Country  : {data['org']} / {data['country']}")
        if data["emails"]:
            ok(f"Emails         : {C_CYAN}{', '.join(data['emails'])}{C_RESET}")
        if data["name_servers"]:
            ok(f"Name Servers   : {', '.join(data['name_servers'][:4])}")

        # Age check
        try:
            raw = w.creation_date
            cd = raw[0] if isinstance(raw, list) else raw
            if cd:
                age_days = (datetime.now() - cd.replace(tzinfo=None)).days
                if age_days < 30:
                    warn(f"{C_RED}⚠  Domain is only {age_days} days old — SUSPICIOUS!{C_RESET}")
                elif age_days < 180:
                    warn(f"Domain is {age_days} days old — relatively new")
                else:
                    ok(f"Domain age: {age_days} days ({age_days // 365} yrs)")
        except Exception:
            pass

    except Exception as e:
        err(f"WHOIS lookup failed: {e}")

# ─── Zone Transfer Check ──────────────────────────────────────────────────────

def zone_transfer_check(domain, results_dict):
    section("⚠️   Zone Transfer Vulnerability Check")
    ns_records = query_records(domain, "NS")
    if not ns_records:
        warn("No NS records found; cannot attempt zone transfer.")
        return

    vulnerable = []
    for ns in ns_records:
        ns = ns.rstrip(".")
        info(f"Attempting AXFR against: {C_YELLOW}{ns}{C_RESET}")
        try:
            z = dns.zone.from_xfr(dns.query.xfr(ns, domain, timeout=5))
            names = list(z.nodes.keys())
            ok(f"{C_RED}⚠ ZONE TRANSFER SUCCESSFUL from {ns}! ({len(names)} records){C_RESET}")
            vulnerable.append({"ns": ns, "record_count": len(names)})
        except Exception:
            ok(f"Zone transfer refused by {ns}  ✓")

    results_dict["zone_transfer"] = {
        "vulnerable": len(vulnerable) > 0,
        "vulnerable_servers": vulnerable,
    }
    if not vulnerable:
        ok("No nameservers are vulnerable to zone transfer.")
    else:
        warn(f"{C_RED}CRITICAL: {len(vulnerable)} nameserver(s) allow zone transfer!{C_RESET}")

# ─── Subdomain Brute-Force ────────────────────────────────────────────────────

def subdomain_brute(domain, results_dict, wordlist=None):
    section("🔍  Subdomain Enumeration")
    subs = wordlist or COMMON_SUBDOMAINS
    found = []

    info(f"Testing {len(subs)} common subdomains...")
    print()

    resolver = dns.resolver.Resolver()
    resolver.timeout = 2
    resolver.lifetime = 2

    for sub in subs:
        fqdn = f"{sub}.{domain}"
        a_records = query_records(fqdn, "A", resolver)
        aaaa_records = query_records(fqdn, "AAAA", resolver)
        if a_records or aaaa_records:
            ips = a_records + aaaa_records
            ok(f"{C_GREEN}{fqdn:<45}{C_RESET} → {C_YELLOW}{', '.join(ips)}{C_RESET}")
            found.append({"subdomain": fqdn, "ips": ips})

    results_dict["subdomains"] = found
    print()
    if found:
        ok(f"Discovered {C_GREEN}{len(found)}{C_RESET} active subdomain(s).")
    else:
        warn("No subdomains found from common list.")

# ─── VirusTotal (optional) ────────────────────────────────────────────────────

def virustotal_check(target, api_key, results_dict):
    section("🛡️   VirusTotal Threat Intelligence")
    if is_ip(target):
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{target}"
    else:
        url = f"https://www.virustotal.com/api/v3/domains/{target}"

    headers = {"x-apikey": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            harmless = stats.get("harmless", 0)
            undetected = stats.get("undetected", 0)
            total = malicious + suspicious + harmless + undetected

            vt_result = {
                "malicious":  malicious,
                "suspicious": suspicious,
                "harmless":   harmless,
                "undetected": undetected,
                "total_engines": total,
                "reputation": attrs.get("reputation", 0),
                "categories": attrs.get("categories", {}),
            }
            results_dict["virustotal"] = vt_result

            bar_m = f"{C_RED}{'█' * malicious}{C_RESET}"
            bar_s = f"{C_YELLOW}{'█' * suspicious}{C_RESET}"
            bar_h = f"{C_GREEN}{'█' * harmless}{C_RESET}"

            ok(f"Malicious  : {C_RED}{malicious:>3}{C_RESET} / {total}  {bar_m}")
            ok(f"Suspicious : {C_YELLOW}{suspicious:>3}{C_RESET} / {total}  {bar_s}")
            ok(f"Harmless   : {C_GREEN}{harmless:>3}{C_RESET} / {total}  {bar_h}")
            ok(f"Reputation : {attrs.get('reputation', 'N/A')}")

            if malicious > 0:
                warn(f"{C_RED}⚠  FLAGGED AS MALICIOUS BY {malicious} ENGINE(S)!{C_RESET}")
            elif suspicious > 0:
                warn(f"{C_YELLOW}⚠  Flagged as suspicious by {suspicious} engine(s).{C_RESET}")
            else:
                ok(f"{C_GREEN}Target appears clean.{C_RESET}")
        elif resp.status_code == 404:
            warn("Not found in VirusTotal database.")
        elif resp.status_code == 401:
            err("Invalid VirusTotal API key.")
        else:
            err(f"VirusTotal API error: {resp.status_code}")
    except Exception as e:
        err(f"VirusTotal request failed: {e}")

# ─── Summary ──────────────────────────────────────────────────────────────────

def print_summary(target, results):
    section("📊  Security Summary")
    ok(f"Target       : {C_YELLOW}{target}{C_RESET}")
    ok(f"Timestamp    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # DNS stats
    dns_recs = results.get("dns_records", {})
    if dns_recs:
        types = ", ".join(dns_recs.keys())
        ok(f"DNS Records  : {C_GREEN}{sum(len(v) for v in dns_recs.values())} records{C_RESET} ({types})")

    # Subdomains
    subs = results.get("subdomains", [])
    if subs:
        ok(f"Subdomains   : {C_GREEN}{len(subs)} discovered{C_RESET}")

    # Zone transfer
    zt = results.get("zone_transfer", {})
    if zt.get("vulnerable"):
        warn(f"Zone Transfer: {C_RED}VULNERABLE ⚠{C_RESET}")
    elif zt:
        ok(f"Zone Transfer: {C_GREEN}Secure ✓{C_RESET}")

    # VT
    vt = results.get("virustotal", {})
    if vt:
        if vt["malicious"] > 0:
            warn(f"Threat Intel : {C_RED}MALICIOUS ({vt['malicious']} detections){C_RESET}")
        else:
            ok(f"Threat Intel : {C_GREEN}Clean{C_RESET}")

    # Geo proxy
    geo = results.get("geolocation", {})
    if geo.get("is_proxy"):
        warn(f"Proxy/VPN    : {C_RED}Detected!{C_RESET}")

    print()

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CyberSec DNS Lookup & Recon Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dns_lookup.py example.com
  python dns_lookup.py example.com --all
  python dns_lookup.py 8.8.8.8 --reverse --geo
  python dns_lookup.py example.com --subdomains --zone-transfer
  python dns_lookup.py example.com --vt-key YOUR_API_KEY --export results.json
        """,
    )
    parser.add_argument("target", help="Domain name or IP address to investigate")
    parser.add_argument("--dns",          action="store_true", help="DNS record enumeration (default: on)")
    parser.add_argument("--reverse",      action="store_true", help="Reverse DNS lookup")
    parser.add_argument("--whois",        action="store_true", help="WHOIS lookup")
    parser.add_argument("--geo",          action="store_true", help="IP Geolocation")
    parser.add_argument("--zone-transfer",action="store_true", help="Test for zone transfer vulnerability")
    parser.add_argument("--subdomains",   action="store_true", help="Subdomain brute-force")
    parser.add_argument("--vt-key",       metavar="API_KEY",   help="VirusTotal API key for threat intel")
    parser.add_argument("--all",          action="store_true", help="Run all checks")
    parser.add_argument("--export",       metavar="FILE",      help="Export results to JSON file")
    parser.add_argument("--no-banner",    action="store_true", help="Suppress banner")

    args = parser.parse_args()

    if not args.no_banner:
        banner()

    target = sanitize(args.target)
    target_is_ip = is_ip(target)

    info(f"Investigating: {C_YELLOW}{target}{C_RESET}  ({'IP address' if target_is_ip else 'Domain'})")
    info(f"Started at   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        "target":    target,
        "type":      "ip" if target_is_ip else "domain",
        "timestamp": datetime.now().isoformat(),
    }

    run_all    = args.all
    run_dns    = run_all or args.dns or not any([
        args.reverse, args.whois, args.geo,
        args.zone_transfer, args.subdomains, args.vt_key
    ])

    # 1. DNS records (domain only)
    if run_dns and not target_is_ip:
        dns_enum(target, results)

    # 2. Resolve domain → IP for further checks
    resolved_ip = None
    if not target_is_ip:
        a_records = query_records(target, "A")
        if a_records:
            resolved_ip = a_records[0]
            info(f"Resolved {target} → {C_YELLOW}{resolved_ip}{C_RESET}")
    else:
        resolved_ip = target

    # 3. Reverse DNS
    if (run_all or args.reverse) and resolved_ip:
        reverse_dns(resolved_ip, results)

    # 4. WHOIS (domain only)
    if (run_all or args.whois) and not target_is_ip:
        whois_lookup(target, results)

    # 5. Geolocation
    if (run_all or args.geo) and resolved_ip:
        geolocate(resolved_ip, results)

    # 6. Zone transfer (domain only)
    if (run_all or args.zone_transfer) and not target_is_ip:
        zone_transfer_check(target, results)

    # 7. Subdomain brute-force (domain only)
    if (run_all or args.subdomains) and not target_is_ip:
        subdomain_brute(target, results)

    # 8. VirusTotal
    if args.vt_key:
        virustotal_check(target, args.vt_key, results)

    # 9. Summary
    print_summary(target, results)

    # 10. Export
    if args.export:
        with open(args.export, "w") as f:
            json.dump(results, f, indent=2, default=str)
        ok(f"Results exported to: {C_CYAN}{args.export}{C_RESET}")
        print()

    return results


if __name__ == "__main__":
    main()
