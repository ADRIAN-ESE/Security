"""Log parsing engine: parses syslog, Apache/Nginx access logs, and generic
level-tagged logs into a unified entry structure.

Supported formats:
- Syslog: "Aug 18 10:23:01 hostname process[pid]: message"
- Apache/Nginx: '192.168.1.1 - - [18/Aug/2026:10:23:01] "GET /path HTTP/1.1" 200'
- Generic ISO: "2026-08-18T10:23:01 [ERROR] message"
"""

import re
import logging
from collections import Counter
from datetime import datetime

logger = logging.getLogger(__name__)

# Regex patterns for different log formats
SYSLOG_RE = re.compile(
    r"^(?P<ts>[A-Z][a-z]{2}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})\s+"
    r"(?P<source>\S+)\s+(?P<msg>.*)$"
)
GENERIC_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s+"
    r"(?:\[(?P<bracket_level>[A-Z]+)\]\s*)?"
    r"(?P<msg>.*)$"
)
APACHE_RE = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d{3})\s+\S+'
)
LEVEL_IN_MSG_RE = re.compile(r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL|TRACE)\b", re.I)

# Get current year for syslog parsing (syslog format doesn't include year)
SYSLOG_YEAR = datetime.now().year


def _guess_level(message, default="UNKNOWN"):
    """Extract log level from message text.
    
    Args:
        message: The log message to analyze
        default: Default level if no level is found
        
    Returns:
        Normalized log level (DEBUG, INFO, WARN, ERROR, CRITICAL, FATAL, TRACE, or default)
    """
    m = LEVEL_IN_MSG_RE.search(message)
    if not m:
        return default
    lvl = m.group(1).upper()
    # Normalize WARNING to WARN
    return "WARN" if lvl == "WARNING" else lvl


def _apache_level(status):
    """Map HTTP status code to log level.
    
    Args:
        status: HTTP status code as string
        
    Returns:
        Log level (ERROR for 5xx, WARN for 4xx, INFO for others)
    """
    s = int(status)
    if s >= 500:
        return "ERROR"
    if s >= 400:
        return "WARN"
    return "INFO"


def parse_line(line):
    """Parse a single log line into a standardized entry dictionary.
    
    Args:
        line: A single line of log text
        
    Returns:
        Dictionary with keys: timestamp, level, source, message
        Returns None if line is empty/whitespace only.
    """
    line = line.rstrip("\n")
    entry = {"timestamp": None, "level": "UNKNOWN", "source": "-", "message": line}
    if not line.strip():
        return None

    # Try syslog format first
    m = SYSLOG_RE.match(line)
    if m:
        entry["timestamp"] = f"{SYSLOG_YEAR} {m.group('ts')}"
        entry["source"] = m.group("source")
        entry["message"] = m.group("msg")
        entry["level"] = _guess_level(entry["message"])
        return entry

    # Try generic ISO/timestamp format
    m = GENERIC_RE.match(line)
    if m:
        entry["timestamp"] = m.group("ts").replace("T", " ")
        entry["message"] = m.group("msg")
        entry["level"] = m.group("bracket_level") or _guess_level(entry["message"])
        entry["level"] = entry["level"].upper()
        if entry["level"] == "WARNING":
            entry["level"] = "WARN"
        return entry

    # Try Apache/Nginx access log format
    m = APACHE_RE.match(line)
    if m:
        entry["timestamp"] = m.group("ts").split()[0]
        entry["source"] = m.group("ip")
        entry["message"] = f'{m.group("method")} {m.group("path")} -> {m.group("status")}'
        entry["level"] = _apache_level(m.group("status"))
        return entry

    # Fallback: guess level from message
    entry["level"] = _guess_level(line)
    return entry


def parse_text(text):
    """Parse a whole log text into a list of entries."""
    entries = []
    for line in text.splitlines():
        e = parse_line(line)
        if e:
            entries.append(e)
    return entries


def _hour_bucket(ts):
    """Normalize various timestamp strings to an hour bucket for the timeline.
    
    Args:
        ts: Timestamp string in various formats
        
    Returns:
        Normalized hour bucket string (e.g., "08-18 10:00")
    """
    if not ts:
        return "unknown"
    
    try:
        # syslog: "2026 Aug 18 10:23:01"
        dt = datetime.strptime(ts, "%Y %b %d %H:%M:%S")
        return dt.strftime("%m-%d %H:00")
    except ValueError:
        pass
    
    # Try ISO format: "2026-08-18T10:23:01"
    m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2})", ts)
    if m:
        return f"{m.group(1)[5:]} {m.group(2)}:00"
    
    # Try Apache format: "18/Aug/2026:10:23:01"
    m = re.match(r"(\d{2})/(\w{3})/(\d{4}):(\d{2})", ts)
    if m:
        return f"{m.group(2)} {m.group(1)} {m.group(4)}:00"
    
    # Fallback
    return ts[:13] if ts else "unknown"


def summarize(entries):
    """Aggregate statistics from parsed entries.
    
    Args:
        entries: List of parsed log entries
        
    Returns:
        Dictionary with aggregated statistics including counts, rates, and top items
    """
    level_counts = Counter(e["level"] for e in entries)
    timeline = Counter(_hour_bucket(e["timestamp"]) for e in entries)
    
    # Extract top error messages (truncated to 120 chars)
    top_errors = Counter(
        e["message"][:120] for e in entries if e["level"] in ("ERROR", "CRITICAL", "FATAL")
    ).most_common(5)
    
    # Extract top sources
    top_sources = Counter(e["source"] for e in entries).most_common(5)
    
    total = len(entries)
    errors = sum(level_counts.get(l, 0) for l in ("ERROR", "CRITICAL", "FATAL"))
    
    return {
        "total": total,
        "errors": errors,
        "warnings": level_counts.get("WARN", 0),
        "error_rate": round(errors / total * 100, 1) if total else 0,
        "level_counts": dict(level_counts),
        "timeline": dict(sorted(timeline.items())),
        "top_errors": top_errors,
        "top_sources": top_sources,
    }
