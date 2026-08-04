"""supabase_widget.py — read-only Supabase queries for dashboard widget + route.

All access is READ-ONLY. Never writes. Uses existing supabase_client env vars.
SECURITY: Never logs SUPABASE_SERVICE_ROLE_KEY.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
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

# Fallback list if information_schema query fails
KNOWN_TABLES = [
    "schools",
    "biz_accounts",
    "biz_invoices",
    "attempts",
    "events",
    "subscriptions",
]

# Whitelist for preview_table — populated dynamically from discovered tables
# Starts with known tables; extended by discover_tables()
ALLOWED_TABLES = set(KNOWN_TABLES)

# Module-level cache so we don't hit information_schema on every request
_discovered_tables: list | None = None


def discover_tables() -> list[str]:
    """Discover all public tables via PostgREST OpenAPI schema endpoint.
    Falls back to KNOWN_TABLES on error. Caches result for process lifetime.
    Returns sorted list of table name strings.
    """
    global _discovered_tables, ALLOWED_TABLES
    if _discovered_tables is not None:
        return _discovered_tables
    if not SUPABASE_URL or not SUPABASE_KEY:
        _discovered_tables = list(KNOWN_TABLES)
        return _discovered_tables
    try:
        # PostgREST exposes an OpenAPI document at /rest/v1/ listing all table paths
        url = f"{SUPABASE_URL}/rest/v1/"
        headers = {**HEADERS, "Accept": "application/openapi+json"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        paths = list(data.get("paths", {}).keys())
        # Filter: no leading /, not empty, not rpc paths, not view-like (views start with v_)
        # We include all — views are still queryable
        names = sorted(
            p.lstrip("/") for p in paths
            if p and p != "/" and not p.startswith("/rpc")
        )
        if not names:
            raise ValueError("OpenAPI returned no table paths")
        _discovered_tables = names
        ALLOWED_TABLES = set(names)
        return _discovered_tables
    except Exception:
        # Fall back to hardcoded list
        _discovered_tables = list(KNOWN_TABLES)
        return _discovered_tables


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
        # Discover all tables via information_schema
        all_tables = discover_tables()
        schools_count = _count_table("schools") if "schools" in all_tables else -1
        # Find most-recent insert across key tables (if they exist)
        latest_ts = None
        for tbl in ["schools", "events", "attempts"]:
            if tbl not in all_tables:
                continue
            ts = _last_created_at(tbl)
            if ts:
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts

        return {
            "project_id": pid,
            "status": "ok",
            "tables_count": len(all_tables),
            "tables_shown": len(all_tables),
            "schools_count": schools_count,
            "last_insert_ts": latest_ts,
        }
    except Exception as e:
        return {"project_id": pid, "status": "error", "error": str(e), "tables_count": 0, "last_insert_ts": None}


_list_tables_cache: tuple[float, list] | None = None
_LIST_TABLES_TTL = 60.0


def list_tables() -> list:
    """Return [{name, rows, last_modified}] for ALL discovered tables.
    Parallelized (20 workers) + 60s cache to keep latency under 2s.
    """
    global _list_tables_cache
    now = time.time()
    if _list_tables_cache and now - _list_tables_cache[0] < _LIST_TABLES_TTL:
        return _list_tables_cache[1]

    all_tables = discover_tables()[:80]

    def fetch(name):
        return {
            "name": name,
            "rows": _count_table(name),
            "last_modified": _last_created_at(name),
        }

    with ThreadPoolExecutor(max_workers=20) as pool:
        result = list(pool.map(fetch, all_tables))

    _list_tables_cache = (now, result)
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
