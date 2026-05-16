"""supabase_widget.py — read-only Supabase queries for dashboard widget + route.

All access is READ-ONLY. Never writes. Uses existing supabase_client env vars.
SECURITY: Never logs SUPABASE_SERVICE_ROLE_KEY.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv("/Volumes/Samsung PSSD T7/AIS-OS/.env")
load_dotenv()

SUPABASE_URL = os.environ.get("EXPO_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "count=exact",
}

# Tables known to exist in the Ag Coach Pro schema
KNOWN_TABLES = [
    "schools",
    "biz_accounts",
    "biz_invoices",
    "attempts",
    "events",
    "subscriptions",
]

# Whitelist for preview_table — prevents injection
ALLOWED_TABLES = set(KNOWN_TABLES)


def _project_id() -> str:
    import re
    # Try direct supabase.co URL
    m = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
    if m:
        return m.group(1)
    # Also check for SUPABASE_PROJECT_ID env
    pid = os.environ.get("SUPABASE_PROJECT_ID", "")
    if pid:
        return pid
    # Fallback: hardcoded from AIS-OS CLAUDE.md
    return "nkoyotdafqllgbpuklva"


def _rest_get(path: str, extra_headers: dict | None = None) -> tuple[list, int]:
    """Make a REST GET. Returns (rows, content-range-count)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials not configured")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {**HEADERS}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        body = json.loads(r.read())
        # Content-Range: 0-9/42 → total=42
        cr = r.headers.get("Content-Range", "")
        total = -1
        if "/" in cr:
            try:
                total = int(cr.split("/")[-1])
            except Exception:
                pass
        return body, total


def _count_table(name: str) -> int:
    """Return row count for a known table. Falls back to -1 on error."""
    try:
        _, total = _rest_get(f"{name}?select=id&limit=1", {"Range": "0-0"})
        return total
    except Exception:
        return -1


def _last_created_at(name: str) -> str | None:
    """Return most-recent created_at from a table, or None."""
    try:
        rows, _ = _rest_get(f"{name}?select=created_at&order=created_at.desc&limit=1")
        if rows:
            return rows[0].get("created_at")
    except Exception:
        pass
    return None


def status() -> dict:
    """Return high-level Supabase status."""
    pid = _project_id()
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"project_id": pid, "status": "error", "error": "Credentials not configured", "tables_count": 0, "last_insert_ts": None}

    try:
        # Try a simple ping
        schools_count = _count_table("schools")
        # Find most-recent insert across key tables
        latest_ts = None
        for tbl in ["schools", "events", "attempts"]:
            ts = _last_created_at(tbl)
            if ts:
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts

        return {
            "project_id": pid,
            "status": "ok",
            "tables_count": len(KNOWN_TABLES),
            "schools_count": schools_count,
            "last_insert_ts": latest_ts,
        }
    except Exception as e:
        return {"project_id": pid, "status": "error", "error": str(e), "tables_count": 0, "last_insert_ts": None}


def list_tables() -> list:
    """Return [{name, rows, last_modified}] for known tables."""
    result = []
    for name in KNOWN_TABLES:
        count = _count_table(name)
        last_ts = _last_created_at(name)
        result.append({
            "name": name,
            "rows": count,
            "last_modified": last_ts,
        })
    return result


def preview_table(name: str, limit: int = 20) -> dict:
    """Return {name, columns, rows} for a whitelisted table (read-only)."""
    if name not in ALLOWED_TABLES:
        raise ValueError(f"Table '{name}' not in allowed list: {sorted(ALLOWED_TABLES)}")
    limit = min(limit, 50)  # cap at 50
    try:
        rows, _ = _rest_get(f"{name}?select=*&limit={limit}")
        columns = list(rows[0].keys()) if rows else []
        # Trim to max 8 columns for display
        if len(columns) > 8:
            columns = columns[:8]
            rows = [{k: r[k] for k in columns} for r in rows]
        return {"name": name, "columns": columns, "rows": rows}
    except Exception as e:
        return {"name": name, "columns": [], "rows": [], "error": str(e)}


def advisors() -> list:
    # MCP-only — stub for now (get_advisors requires Claude Code MCP, not available from server)
    return []
