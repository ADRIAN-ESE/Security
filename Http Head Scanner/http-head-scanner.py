import httpx
import json
import sys
from datetime import datetime

SECURITY_HEADERS = {
    "strict-transport-security": {
        "desc": "Enforces HTTPS connections (HSTS)",
        "severity": "high"
    },
    "content-security-policy": {
        "desc": "Prevents XSS and injection attacks",
        "severity": "high"
    },
    "x-frame-options": {
        "desc": "Protects against clickjacking",
        "severity": "medium"
    },
    "x-content-type-options": {
        "desc": "Prevents MIME-type sniffing",
        "severity": "medium"
    },
    "referrer-policy": {
        "desc": "Controls referrer information sent",
        "severity": "low"
    },
    "permissions-policy": {
        "desc": "Controls browser feature access",
        "severity": "low"
    },
    "x-xss-protection": {
        "desc": "Legacy XSS filter (older browsers)",
        "severity": "low"
    },
    "cache-control": {
        "desc": "Controls caching behavior",
        "severity": "low"
    },
    "cross-origin-opener-policy": {
        "desc": "Isolates browsing context",
        "severity": "medium"
    },
    "cross-origin-resource-policy": {
        "desc": "Controls cross-origin resource sharing",
        "severity": "medium"
    },
}


def scan_headers(url: str, timeout: int = 10) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status_code": None,
        "all_headers": {},
        "security_analysis": {},
        "score": 0,
        "error": None,
    }

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(url)
            result["status_code"] = response.status_code
            result["final_url"] = str(response.url)
            result["all_headers"] = dict(response.headers)

            present = 0
            for header, meta in SECURITY_HEADERS.items():
                found = header in response.headers
                result["security_analysis"][header] = {
                    "present": found,
                    "value": response.headers.get(header, None),
                    "description": meta["desc"],
                    "severity": meta["severity"],
                }
                if found:
                    present += 1

            result["score"] = round((present / len(SECURITY_HEADERS)) * 100)

    except httpx.ConnectError:
        result["error"] = f"Could not connect to {url}"
    except httpx.TimeoutException:
        result["error"] = f"Request timed out after {timeout}s"
    except Exception as e:
        result["error"] = str(e)

    return result


def print_report(result: dict):
    sep = "=" * 60
    print(f"\n{sep}")
    print("  HTTP HEADERS SCANNER REPORT")
    print(sep)

    if result["error"]:
        print(f"\n  ❌ Error: {result['error']}")
        return

    print(f"\n  URL        : {result['url']}")
    print(f"  Final URL  : {result.get('final_url', result['url'])}")
    print(f"  Status     : {result['status_code']}")
    print(f"  Scanned at : {result['timestamp']}")
    print(f"  Security   : {result['score']}% ({result['score']}/100)")

    print(f"\n{'-' * 60}")
    print("  SECURITY HEADERS")
    print(f"{'-' * 60}")

    for header, info in result["security_analysis"].items():
        icon = "✅" if info["present"] else "❌"
        severity_tag = f"[{info['severity'].upper()}]"
        print(f"\n  {icon} {header}")
        print(f"     {severity_tag} {info['description']}")
        if info["present"]:
            val = info["value"]
            if len(val) > 70:
                val = val[:67] + "..."
            print(f"     Value: {val}")

    print(f"\n{'-' * 60}")
    print("  ALL RESPONSE HEADERS")
    print(f"{'-' * 60}")
    for k, v in result["all_headers"].items():
        print(f"  {k}: {v}")

    print(f"\n{sep}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        url = input("Enter URL to scan: ").strip()
    else:
        url = sys.argv[1]

    print(f"\nScanning {url} ...")
    result = scan_headers(url)
    print_report(result)

    # Optionally save JSON
    out_file = "scan_result.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Full JSON saved to: {out_file}\n")