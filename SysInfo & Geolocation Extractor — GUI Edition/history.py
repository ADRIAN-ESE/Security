"""history.py — Scan history persistence & comparison helpers."""

import json
import os
import datetime
from typing import Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "scan_history.json")
MAX_HISTORY  = 20


def _load_raw() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_raw(data: list):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_scan(report_dict: dict):
    """Append a report dict to history (capped at MAX_HISTORY)."""
    data = _load_raw()
    data.append(report_dict)
    data = data[-MAX_HISTORY:]
    _save_raw(data)


def load_history() -> list:
    """Return all saved reports as list of dicts, newest first."""
    return list(reversed(_load_raw()))


def delete_scan(index: int):
    """Delete by index in the load_history() order (newest-first)."""
    data = _load_raw()
    reversed_idx = len(data) - 1 - index
    if 0 <= reversed_idx < len(data):
        data.pop(reversed_idx)
        _save_raw(data)


def clear_history():
    _save_raw([])


def compare_reports(a: dict, b: dict) -> list[dict]:
    """
    Return a list of diffs between two reports.
    Each item: {section, field, old, new, changed}
    """
    diffs = []

    def flat(d: dict, prefix="") -> dict:
        out = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(flat(v, key))
            elif isinstance(v, list):
                out[key] = str(v)
            else:
                out[key] = v
        return out

    fa, fb = flat(a), flat(b)
    all_keys = sorted(set(fa) | set(fb))

    skip = {"generated_at"}

    for k in all_keys:
        if k in skip:
            continue
        va = fa.get(k, "—")
        vb = fb.get(k, "—")
        diffs.append({
            "field":   k,
            "old":     str(va),
            "new":     str(vb),
            "changed": str(va) != str(vb),
        })

    return diffs


def summary_label(report_dict: dict) -> str:
    ts  = report_dict.get("generated_at", "Unknown time")
    sys = report_dict.get("system", {})
    host = sys.get("hostname", "unknown")
    ip   = report_dict.get("geo", {}).get("public_ip", "?")
    return f"{ts}  |  {host}  |  {ip}"
