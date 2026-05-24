"""usage_tracker.py — Live token usage tracking across AI subscriptions.

Parses ~/.claude/projects/**/*.jsonl for last 30 days.
Computes token consumption per subscription and API-equivalent value.

Token fields in .jsonl assistant usage events:
  input_tokens               — non-cached prompt tokens
  cache_read_input_tokens    — prompt tokens served from cache (NOT counted as new usage)
  cache_creation_input_tokens— tokens written to cache (counted as input cost)
  output_tokens              — completion tokens

Claude Pro Max: rate-limited per 5-hour window, no hard monthly ceiling.
  → We show usage in the CURRENT 5-hour window, not a % of plan.
ChatGPT/Gemini: Bryan uses subscriptions (not API), so no raw token events exist.
  → Show "Manual — subscription only" rather than fake 0%.

Budget: ~5s typical. Safe to call on every /api/usage hit.
"""
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from pathlib import Path as _Path

# Allow import whether running as script or module
_HERE = _Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from pricing import compute_api_cost

HOME = Path.home()
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_ROOT = HOME / ".claude" / "projects"
CODEX_LOGS_DB = HOME / ".codex" / "logs_2.sqlite"
CODEX_AUTH_FILE = HOME / ".codex" / "auth.json"
CODEX_CONFIG_FILE = HOME / ".codex" / "config.toml"
GEMINI_ROOT = HOME / ".gemini"
HERMES_STATE_DB = Path(
    os.environ.get("HERMES_STATE_DB")
    or os.environ.get("AIOS_HERMES_STATE_DB")
    or str(HOME / ".hermes" / "state.db")
).expanduser()
OPENROUTER_API_BASE = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1").rstrip("/")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")

# ── Subscriptions ───────────────────────────────────────────────
# plan_tokens = None means "no hard ceiling, rate-limited"
SUBSCRIPTIONS = [
    {
        "name": "Claude Max 5x",
        "monthly_usd": float(os.environ.get("CLAUDE_MAX_MONTHLY_USD", "100")),
        "model_family": "claude",
        "plan_tokens": None,          # rate-limited per 5h window, not monthly
        "rate_limit_note": "Rate-limited per 5-hour window; set CLAUDE_MAX_MONTHLY_USD=200 for Max 20x",
    },
    {
        "name": "ChatGPT Plus",
        "monthly_usd": float(os.environ.get("CHATGPT_MONTHLY_USD", "20")),
        "model_family": "openai",
        "plan_tokens": None,          # subscription, no API events tracked here
        "rate_limit_note": "Subscription — track usage in ChatGPT",
    },
    {
        "name": "Gemini Advanced",
        "monthly_usd": float(os.environ.get("GEMINI_MONTHLY_USD", "21.31")),
        "model_family": "gemini",
        "plan_tokens": None,
        "rate_limit_note": "Subscription — track usage in Gemini",
    },
]

AI_VENDOR_PATTERNS = [
    ("anthropic", re.compile(r"anthropic|claude", re.I)),
    ("openrouter", re.compile(r"openrouter", re.I)),
    ("openai", re.compile(r"openai|chatgpt", re.I)),
    ("google_gemini", re.compile(r"google|gemini", re.I)),
]

KNOWN_AI_CONFIGS = [
    ("AIS-OS .env", BASE_DIR.parent / ".env"),
    ("AgCoach local .env", HOME / ".agcoach" / ".env"),
    ("Hermes config", HOME / ".hermes" / "config.yaml"),
    ("Hermes repo .env", Path("/Volumes/Samsung PSSD T7/hermes-claw/.env")),
    ("Codex auth", CODEX_AUTH_FILE),
    ("Codex config", CODEX_CONFIG_FILE),
    ("Gemini OAuth", GEMINI_ROOT / "oauth_creds.json"),
    ("Gemini accounts", GEMINI_ROOT / "google_accounts.json"),
]

# ── API pricing per 1M tokens (in/out) ────────────────────────
API_RATES = {
    "claude-opus":   {"input_per_1m": 5.0,   "output_per_1m": 25.0},
    "claude-sonnet": {"input_per_1m": 3.0,   "output_per_1m": 15.0},
    "claude-haiku":  {"input_per_1m": 1.0,   "output_per_1m": 5.0},
    "gpt-5":         {"input_per_1m": 5.0,   "output_per_1m": 15.0},
    "gpt-4o":        {"input_per_1m": 2.5,   "output_per_1m": 10.0},
    "gemini":        {"input_per_1m": 1.25,  "output_per_1m": 5.0},
}

FAMILY_DEFAULT_RATES = {
    "claude": {"input_per_1m": 3.0,  "output_per_1m": 15.0},
    "openai": {"input_per_1m": 5.0,  "output_per_1m": 15.0},
    "gemini": {"input_per_1m": 1.25, "output_per_1m": 5.0},
}


def _get_rate_for_model(model_str: str, family: str) -> dict:
    m = (model_str or "").lower()
    if "opus" in m:   return API_RATES["claude-opus"]
    if "haiku" in m:  return API_RATES["claude-haiku"]
    if "sonnet" in m: return API_RATES["claude-sonnet"]
    if "gpt-5" in m:  return API_RATES["gpt-5"]
    if "gpt-4" in m:  return API_RATES["gpt-4o"]
    if "gemini" in m: return API_RATES["gemini"]
    return FAMILY_DEFAULT_RATES.get(family, {"input_per_1m": 3.0, "output_per_1m": 15.0})


def _classify_model(model_str: str) -> str:
    m = (model_str or "").lower()
    if any(k in m for k in ("claude", "anthropic")):
        return "claude"
    if any(k in m for k in ("gpt", "openai", "chatgpt", "o1", "o3", "o4")):
        return "openai"
    if "gemini" in m:
        return "gemini"
    return "claude"  # default — Claude Code is the main tool


def _classify_provider_model(provider: str, model: str) -> str:
    """Classify by explicit provider first, then model slug."""
    p = (provider or "").lower()
    if p in {"anthropic", "claude"}:
        return "claude"
    if p in {"openai", "openai-codex", "chatgpt"}:
        return "openai"
    if "gemini" in p or p == "google":
        return "gemini"
    return _classify_model(model)


def _days_left_in_cycle() -> int:
    now = datetime.now()
    import calendar
    last_day = calendar.monthrange(now.year, now.month)[1]
    return last_day - now.day


def _iter_recent_events(days: int = 30):
    """Yield (file_path, event_dict) for jsonl events within the last N days."""
    if not PROJECTS_ROOT.exists():
        return
    cutoff = time.time() - days * 86400
    for p in PROJECTS_ROOT.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < cutoff:
                continue
            with open(p) as fh:
                for line in fh:
                    try:
                        ev = json.loads(line)
                        yield p, ev
                    except Exception:
                        continue
        except Exception:
            continue


def _iter_events_since_ts(since_ts: float):
    """Yield (file_path, event_dict, event_timestamp) for events after since_ts."""
    if not PROJECTS_ROOT.exists():
        return
    cutoff_day = time.time() - 1 * 86400  # only scan files modified in last 24h for 5h window
    for p in PROJECTS_ROOT.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < cutoff_day:
                continue
            with open(p) as fh:
                for line in fh:
                    try:
                        ev = json.loads(line)
                        ts_str = ev.get("timestamp") or ""
                        if not ts_str:
                            continue
                        # Parse ISO timestamp
                        try:
                            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts = dt.timestamp()
                        except Exception:
                            continue
                        if ts >= since_ts:
                            yield p, ev, ts
                    except Exception:
                        continue
        except Exception:
            continue


def _build_daily_burn(daily_tokens: dict, days: int = 14) -> list:
    result = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": d, "tokens": daily_tokens.get(d, 0)})
    return result


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def _read_env_value(name: str) -> tuple[str, str] | tuple[None, None]:
    val = os.environ.get(name, "").strip()
    if val:
        return val, "environment"
    for _, path in KNOWN_AI_CONFIGS:
        path = Path(path).expanduser()
        if not path.exists() or path.suffix == ".json":
            continue
        try:
            for line in path.read_text(errors="ignore").splitlines():
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, raw = line.split("=", 1)
                if key.strip() == name:
                    raw = raw.strip().strip('"').strip("'")
                    if raw:
                        return raw, str(path)
        except Exception:
            continue
    return None, None


def _http_get_json(base_url: str, path: str, key: str, params: dict | None = None, extra_headers: dict | None = None) -> dict:
    query = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"{base_url}{path}" + (f"?{query}" if query else "")
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update({k: v for k, v in extra_headers.items() if v})
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")[:500]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code}: {body or exc.reason}") from exc


def _parse_card_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _load_expense_doc() -> dict:
    path = DATA_DIR / "expenses.json"
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _provider_for_merchant(merchant: str) -> str | None:
    for provider, pattern in AI_VENDOR_PATTERNS:
        if pattern.search(merchant or ""):
            return provider
    return None


def _build_ai_card_spend(days: int = 30) -> dict:
    """Actual imported card charges for AI vendors.

    Apple Card imports are not always current to today's date, so the rolling
    window is anchored to the newest imported transaction date. That keeps the
    table honest instead of showing $0 just because May has not been imported.
    """
    doc = _load_expense_doc()
    rows = doc.get("expenses_full") or []
    parsed = []
    for row in rows:
        dt = _parse_card_date(row.get("date", ""))
        provider = _provider_for_merchant(row.get("merchant", ""))
        if not dt or not provider:
            continue
        parsed.append((dt, provider, row))

    if not parsed:
        return {
            "window_label": "No card import",
            "window_start": None,
            "window_end": None,
            "total_usd": 0.0,
            "by_provider": {},
            "charges": [],
        }

    newest = max(dt for dt, _, _ in parsed)
    cutoff = newest - timedelta(days=days)
    by_provider = defaultdict(float)
    charges = []
    for dt, provider, row in parsed:
        if dt < cutoff:
            continue
        amount = _safe_float(row.get("amount"))
        by_provider[provider] += amount
        charges.append({
            "date": dt.strftime("%Y-%m-%d"),
            "provider": provider,
            "merchant": row.get("merchant", ""),
            "amount_usd": round(amount, 2),
            "business": row.get("business", ""),
        })

    charges.sort(key=lambda r: r["date"], reverse=True)
    by_provider = {k: round(v, 2) for k, v in sorted(by_provider.items(), key=lambda x: -x[1])}
    return {
        "window_label": f"Last {days} days in imported card data",
        "window_start": cutoff.strftime("%Y-%m-%d"),
        "window_end": newest.strftime("%Y-%m-%d"),
        "total_usd": round(sum(by_provider.values()), 2),
        "by_provider": by_provider,
        "charges": charges[:40],
    }


def _build_daily_card_spend(card_window: dict) -> list:
    start = card_window.get("window_start")
    end = card_window.get("window_end")
    if not start or not end:
        return []
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return []
    by_day = defaultdict(float)
    for charge in card_window.get("charges", []):
        by_day[charge.get("date", "")] += _safe_float(charge.get("amount_usd"))
    out = []
    cur = start_dt
    while cur <= end_dt:
        key = cur.strftime("%Y-%m-%d")
        out.append({"date": key, "usd": round(by_day.get(key, 0.0), 2)})
        cur += timedelta(days=1)
    return out


def _scan_key_inventory() -> list:
    """List AI auth material that exists locally without returning secret values."""
    inventory = []

    def add(source, path, kind, provider, status="found", detail=""):
        inventory.append({
            "source": source,
            "path": str(path),
            "kind": kind,
            "provider": provider,
            "status": status,
            "detail": detail,
        })

    env_key_re = re.compile(r"^\s*([A-Z0-9_]*(?:API_KEY|TOKEN|ACCESS_TOKEN|AUTH_TOKEN|SECRET)[A-Z0-9_]*)\s*=")
    provider_re = re.compile(r"(OPENAI|ANTHROPIC|CLAUDE|OPENROUTER|GEMINI|GOOGLE|HERMES|CODEX|PINECONE)", re.I)
    for label, path in KNOWN_AI_CONFIGS:
        path = Path(path).expanduser()
        if not path.exists():
            add(label, path, "config", "unknown", "missing", "file not present")
            continue
        if path.suffix == ".json":
            try:
                data = json.loads(path.read_text())
            except Exception:
                data = {}
            if "tokens" in data or "oauth" in path.name.lower() or "accounts" in path.name.lower():
                provider = "codex/openai" if "codex" in label.lower() else "gemini/google"
                add(label, path, "oauth", provider, "found", "OAuth/account file present")
            elif any(provider_re.search(str(k)) for k in data.keys()):
                add(label, path, "config", "ai", "found", "AI config keys present")
            else:
                add(label, path, "config", "unknown", "found", "file present")
            continue
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            add(label, path, "config", "unknown", "unreadable", "could not read file")
            continue
        keys = []
        for line in text.splitlines():
            match = env_key_re.match(line)
            if match and provider_re.search(match.group(1)):
                keys.append(match.group(1))
        if keys:
            for key_name in sorted(set(keys)):
                provider_match = provider_re.search(key_name)
                provider = provider_match.group(1).lower() if provider_match else "ai"
                add(label, path, "api_key", provider, "found", key_name)
        elif provider_re.search(text):
            add(label, path, "config", "ai", "found", "AI provider config present")
        else:
            add(label, path, "config", "unknown", "found", "file present")
    return inventory


def _iter_codex_response_usage(days: int = 30):
    if not CODEX_LOGS_DB.exists():
        return
    cutoff = int(time.time() - days * 86400)
    conn = None
    seen = set()
    try:
        conn = sqlite3.connect(f"file:{CODEX_LOGS_DB}?mode=ro", uri=True, timeout=1.0)
        rows = conn.execute(
            """
            SELECT ts, feedback_log_body
            FROM logs
            WHERE ts >= ? AND feedback_log_body LIKE '%response.completed%'
            ORDER BY ts DESC
            """,
            (cutoff,),
        )
        for ts, body in rows:
            if not body:
                continue
            idx = body.find("{")
            if idx < 0:
                continue
            try:
                payload = json.loads(body[idx:])
            except Exception:
                continue
            response = payload.get("response") or {}
            usage = response.get("usage") or {}
            response_id = response.get("id") or f"{ts}:{json.dumps(usage, sort_keys=True)}"
            if response_id in seen:
                continue
            seen.add(response_id)
            if usage:
                yield {
                    "timestamp": ts,
                    "response_id": response_id,
                    "model": response.get("model") or payload.get("model") or "codex/openai",
                    "usage": usage,
                }
    except Exception:
        return
    finally:
        if conn is not None:
            conn.close()


def _gemini_local_status() -> dict:
    history_root = GEMINI_ROOT / "history"
    project_count = 0
    file_count = 0
    if history_root.exists():
        for p in history_root.iterdir():
            if p.is_dir():
                project_count += 1
        for p in history_root.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                file_count += 1
    return {
        "sessions": project_count,
        "files": file_count,
        "oauth_present": (GEMINI_ROOT / "oauth_creds.json").exists(),
    }


def _per_session_top(session_tokens: dict, top_n: int = 10) -> list:
    sorted_sessions = sorted(session_tokens.items(), key=lambda x: x[1], reverse=True)
    return [{"session_id": sid[:24], "tokens": tok} for sid, tok in sorted_sessions[:top_n]]


def _session_key(source: str, session_id: str) -> str:
    return f"{source}:{session_id}"


def _budget_float(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        val = float(raw)
        return val if val > 0 else None
    except ValueError:
        return None


def _budget_int(name: str) -> int | None:
    val = _budget_float(name)
    return int(val) if val is not None else None


def _build_budget_status(total_tokens_30d: int, total_cost_30d: float, daily_tokens: dict, daily_cost: dict) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    daily_token_limit = _budget_int("AIOS_DAILY_TOKEN_LIMIT")
    monthly_token_limit = _budget_int("AIOS_MONTHLY_TOKEN_LIMIT")
    daily_cost_limit = _budget_float("AIOS_DAILY_COST_LIMIT_USD")
    monthly_cost_limit = _budget_float("AIOS_MONTHLY_COST_LIMIT_USD")

    def entry(label, used, limit, unit):
        if limit is None:
            return {"label": label, "used": used, "limit": None, "unit": unit, "pct": None, "status": "unset"}
        pct = round((used / limit) * 100, 1) if limit else 0
        status = "over" if used > limit else "warn" if pct >= 80 else "ok"
        return {"label": label, "used": round(used, 2), "limit": limit, "unit": unit, "pct": pct, "status": status}

    return {
        "daily_tokens": entry("Daily tokens", daily_tokens.get(today, 0), daily_token_limit, "tokens"),
        "monthly_tokens": entry("30d tokens", total_tokens_30d, monthly_token_limit, "tokens"),
        "daily_cost": entry("Daily AI cost", daily_cost.get(today, 0.0), daily_cost_limit, "usd"),
        "monthly_cost": entry("30d AI cost", total_cost_30d, monthly_cost_limit, "usd"),
        "env_knobs": {
            "AIOS_DAILY_TOKEN_LIMIT": daily_token_limit,
            "AIOS_MONTHLY_TOKEN_LIMIT": monthly_token_limit,
            "AIOS_DAILY_COST_LIMIT_USD": daily_cost_limit,
            "AIOS_MONTHLY_COST_LIMIT_USD": monthly_cost_limit,
        },
    }


def _iter_hermes_sessions(days: int = 30):
    """Yield normalized token/cost rows from Hermes state.db.

    Hermes already records provider-normalized token counters in its sessions
    table. AIS-OS reads those totals directly so Hermes is included in the same
    dashboard as local Claude Code usage.
    """
    if not HERMES_STATE_DB.exists():
        return
    cutoff = time.time() - days * 86400
    conn = None
    try:
        uri = f"file:{HERMES_STATE_DB}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=1.0)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, source, model, billing_provider, billing_base_url,
                   started_at, ended_at,
                   input_tokens, output_tokens, cache_read_tokens,
                   cache_write_tokens, reasoning_tokens, api_call_count,
                   estimated_cost_usd, actual_cost_usd, cost_status, cost_source
            FROM sessions
            WHERE COALESCE(ended_at, started_at, 0) >= ?
            """,
            (cutoff,),
        ).fetchall()
        for row in rows:
            yield dict(row)
    except Exception:
        return
    finally:
        if conn is not None:
            conn.close()


def _fetch_openrouter_account_usage() -> dict | None:
    """Fetch OpenRouter account/key spend if OPENROUTER_API_KEY is configured."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }

    def get_json(path: str) -> dict:
        req = urllib.request.Request(f"{OPENROUTER_API_BASE}{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        credits = (get_json("/credits") or {}).get("data") or {}
        try:
            key_data = (get_json("/key") or {}).get("data") or {}
        except Exception:
            key_data = {}
    except Exception as exc:
        return {
            "configured": True,
            "ok": False,
            "error": str(exc)[:200],
            "base_url": OPENROUTER_API_BASE,
        }

    total_credits = float(credits.get("total_credits") or 0.0)
    total_usage = float(credits.get("total_usage") or 0.0)
    limit = key_data.get("limit")
    remaining = key_data.get("limit_remaining")
    usage = key_data.get("usage")
    return {
        "configured": True,
        "ok": True,
        "base_url": OPENROUTER_API_BASE,
        "total_credits_usd": round(total_credits, 4),
        "total_usage_usd": round(total_usage, 4),
        "balance_usd": round(max(0.0, total_credits - total_usage), 4),
        "key_limit_usd": limit if isinstance(limit, (int, float)) else None,
        "key_remaining_usd": remaining if isinstance(remaining, (int, float)) else None,
        "key_usage_usd": round(float(usage), 4) if isinstance(usage, (int, float)) else None,
        "usage_daily_usd": round(float(key_data.get("usage_daily")), 4) if isinstance(key_data.get("usage_daily"), (int, float)) else None,
        "usage_weekly_usd": round(float(key_data.get("usage_weekly")), 4) if isinstance(key_data.get("usage_weekly"), (int, float)) else None,
        "usage_monthly_usd": round(float(key_data.get("usage_monthly")), 4) if isinstance(key_data.get("usage_monthly"), (int, float)) else None,
        "limit_reset": key_data.get("limit_reset"),
    }


def _fetch_openai_account_usage(days: int = 30) -> dict:
    """Fetch actual OpenAI Platform costs/usage when an Admin key is available.

    OpenAI's Costs endpoint is the authoritative billing figure. Normal project
    API keys may be able to run model calls but can be denied organization-level
    costs; when that happens, return a visible dashboard gap instead of $0.
    """
    key, source = _read_env_value("OPENAI_ADMIN_KEY")
    key_name = "OPENAI_ADMIN_KEY"
    if not key:
        key, source = _read_env_value("OPENAI_API_KEY")
        key_name = "OPENAI_API_KEY"
    if not key:
        return {"configured": False, "ok": False, "source": None}

    end_ts = int(time.time())
    start_ts = end_ts - days * 86400
    extra_headers = {
        "OpenAI-Organization": os.environ.get("OPENAI_ORG_ID", "").strip(),
        "OpenAI-Project": os.environ.get("OPENAI_PROJECT_ID", "").strip(),
    }

    account = {
        "configured": True,
        "ok": False,
        "source": source,
        "key_name": key_name,
        "key_scope": "admin" if key.startswith("sk-admin") else "project_or_user",
        "base_url": OPENAI_API_BASE,
    }

    def bucket_results(doc: dict) -> list:
        out = []
        for bucket in doc.get("data", []) or []:
            for result in bucket.get("results", []) or []:
                out.append((bucket, result))
        return out

    try:
        costs_doc = _http_get_json(
            OPENAI_API_BASE,
            "/organization/costs",
            key,
            {
                "start_time": start_ts,
                "end_time": end_ts,
                "bucket_width": "1d",
                "group_by": ["line_item"],
            },
            extra_headers,
        )
    except Exception as exc:
        account["error"] = str(exc)[:260]
        account["message"] = (
            "OpenAI key found, but organization cost lookup failed. "
            "Use an OpenAI Admin key with Usage/Costs read access as OPENAI_ADMIN_KEY."
        )
        return account

    total_cost = 0.0
    by_line_item = defaultdict(float)
    daily_cost = defaultdict(float)
    for bucket, result in bucket_results(costs_doc):
        amount = result.get("amount") or {}
        cost = _safe_float(amount.get("value"))
        total_cost += cost
        label = result.get("line_item") or "OpenAI API"
        by_line_item[label] += cost
        start = bucket.get("start_time")
        if start:
            daily_cost[datetime.fromtimestamp(int(start)).strftime("%Y-%m-%d")] += cost

    usage_summary = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "requests": 0,
        "by_model": {},
    }
    try:
        usage_doc = _http_get_json(
            OPENAI_API_BASE,
            "/organization/usage/completions",
            key,
            {
                "start_time": start_ts,
                "end_time": end_ts,
                "bucket_width": "1d",
                "group_by": ["model"],
            },
            extra_headers,
        )
        model_totals = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "requests": 0})
        for _, result in bucket_results(usage_doc):
            model = result.get("model") or "unknown"
            inp = int(result.get("input_tokens") or 0)
            out = int(result.get("output_tokens") or 0)
            cached = int(result.get("input_cached_tokens") or result.get("cached_tokens") or 0)
            reqs = int(result.get("num_model_requests") or 0)
            usage_summary["input_tokens"] += inp
            usage_summary["output_tokens"] += out
            usage_summary["cached_tokens"] += cached
            usage_summary["requests"] += reqs
            model_totals[model]["input_tokens"] += inp
            model_totals[model]["output_tokens"] += out
            model_totals[model]["cached_tokens"] += cached
            model_totals[model]["requests"] += reqs
        usage_summary["by_model"] = {
            k: v for k, v in sorted(
                model_totals.items(),
                key=lambda item: item[1]["input_tokens"] + item[1]["output_tokens"],
                reverse=True,
            )[:12]
        }
    except Exception as exc:
        usage_summary["error"] = str(exc)[:260]

    return {
        **account,
        "ok": True,
        "total_cost_usd": round(total_cost, 4),
        "by_line_item": {k: round(v, 4) for k, v in sorted(by_line_item.items(), key=lambda x: -x[1])},
        "daily_cost_usd": [
            {"date": k, "usd": round(v, 4)}
            for k, v in sorted(daily_cost.items())
        ],
        "usage": usage_summary,
    }


def _five_hour_window_stats() -> dict:
    """Compute Claude token usage in the current 5-hour window."""
    now = time.time()
    window_start = now - 5 * 3600
    inp = 0
    out = 0
    cache_read = 0
    cache_create = 0
    events = 0
    for _, ev, _ in _iter_events_since_ts(window_start):
        msg = ev.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        usage = msg.get("usage") or {}
        if not usage:
            continue
        family = _classify_model(msg.get("model", "") or "")
        if family != "claude":
            continue
        inp += usage.get("input_tokens", 0) or 0
        out += usage.get("output_tokens", 0) or 0
        cache_read += usage.get("cache_read_input_tokens", 0) or 0
        cache_create += usage.get("cache_creation_input_tokens", 0) or 0
        events += 1
    return {
        "input_tokens": inp,
        "output_tokens": out,
        "cache_read_tokens": cache_read,
        "cache_creation_tokens": cache_create,
        "total_tokens": inp + out + cache_create,  # cache_read is free re-reads
        "events": events,
        "window_hours": 5,
    }


def _per_model_breakdown(family_model_tokens: dict) -> dict:
    """Return {model_key: {input, output, cache_read, cache_create}} per model."""
    out = {}
    for model_key, tok in family_model_tokens.items():
        out[model_key] = tok
    return out


def usage_stats() -> dict:
    """Returns usage data for all subscriptions plus detailed breakdown.

    Key changes from v1:
    - input_tokens = non-cached prompt tokens ONLY (not added to cache_read)
    - cache_read_input_tokens tracked separately (informational — Claude caches these, no extra billing cost)
    - cache_creation_input_tokens tracked separately (these ARE billed as input)
    - Claude Pro Max: no % of plan, shows 5h window instead
    - ChatGPT/Gemini: shows "Manual entry" note, no fake 0% bars
    - Per-model breakdown (opus/sonnet/haiku)
    """
    # Accumulators
    family_input = defaultdict(int)         # family -> non-cached input tokens
    family_output = defaultdict(int)        # family -> output tokens
    family_cache_read = defaultdict(int)    # family -> cache read tokens (informational)
    family_cache_create = defaultdict(int)  # family -> cache creation tokens (billed as input)
    family_models = defaultdict(set)        # family -> set of model strings seen
    model_tokens = defaultdict(lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0})
    daily_tokens = defaultdict(int)         # "YYYY-MM-DD" -> tokens (input+output+cache_create)
    daily_cost = defaultdict(float)         # "YYYY-MM-DD" -> actual/estimated cost
    session_tokens = defaultdict(int)
    sessions_seen = set()
    source_breakdown = defaultdict(lambda: {
        "sessions": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "reasoning_tokens": 0,
        "billable_tokens": 0,
        "estimated_cost_usd": 0.0,
        "actual_cost_usd": 0.0,
        "api_calls": 0,
    })
    data_quality = []

    for fpath, ev in _iter_recent_events(days=30):
        msg = ev.get("message") or {}
        role = msg.get("role", "")
        model = msg.get("model", "") or ""
        usage = msg.get("usage") or {}

        sid = ev.get("sessionId") or str(fpath)
        sessions_seen.add(sid)

        if role == "assistant" and usage:
            inp = usage.get("input_tokens", 0) or 0
            out = usage.get("output_tokens", 0) or 0
            cr = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation_input_tokens", 0) or 0
            family = _classify_model(model)
            family_input[family] += inp
            family_output[family] += out
            family_cache_read[family] += cr
            family_cache_create[family] += cc
            if model and (inp or out or cr or cc):
                family_models[family].add(model)
                # Per-model breakdown key
                mk = model.split("-")[0:2]
                model_key = "-".join(mk)[:20] if mk else model[:20]
                model_tokens[model_key]["input"] += inp
                model_tokens[model_key]["output"] += out
                model_tokens[model_key]["cache_read"] += cr
                model_tokens[model_key]["cache_create"] += cc

            # Billable tokens for burn tracking: input + output + cache_creation
            # (cache_read is served from cache at reduced cost, not a new ingest)
            billable = inp + out + cc
            call_cost = compute_api_cost(
                input_tokens=inp,
                output_tokens=out,
                cache_creation_tokens=cc,
                cache_read_tokens=cr,
                model_str=model,
            )
            source_breakdown["claude_code"]["sessions"] = len(sessions_seen)
            source_breakdown["claude_code"]["input_tokens"] += inp
            source_breakdown["claude_code"]["output_tokens"] += out
            source_breakdown["claude_code"]["cache_read_tokens"] += cr
            source_breakdown["claude_code"]["cache_creation_tokens"] += cc
            source_breakdown["claude_code"]["billable_tokens"] += billable
            source_breakdown["claude_code"]["estimated_cost_usd"] += call_cost
            if billable > 0:
                ts_str = ev.get("timestamp") or ""
                if ts_str:
                    try:
                        day = ts_str[:10]
                        daily_tokens[day] += billable
                        daily_cost[day] += call_cost
                    except Exception:
                        pass
                session_tokens[sid] += billable

    codex_events = list(_iter_codex_response_usage(days=30) or [])
    if CODEX_LOGS_DB.exists():
        source_breakdown["codex"]["db_path"] = str(CODEX_LOGS_DB)
        source_breakdown["codex"]["sessions"] = len(codex_events)
    else:
        data_quality.append({
            "source": "codex",
            "status": "missing",
            "message": f"Codex local log DB not found at {CODEX_LOGS_DB}",
        })

    for ev in codex_events:
        usage = ev.get("usage") or {}
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        details_in = usage.get("input_tokens_details") or {}
        details_out = usage.get("output_tokens_details") or {}
        cached = int(details_in.get("cached_tokens") or 0)
        reasoning = int(details_out.get("reasoning_tokens") or 0)
        model = ev.get("model") or "codex/openai"
        billable = inp + out
        family = "openai"
        call_cost = compute_api_cost(
            input_tokens=max(0, inp - cached),
            output_tokens=out,
            cache_creation_tokens=0,
            cache_read_tokens=cached,
            model_str=model,
        )

        family_input[family] += inp
        family_output[family] += out
        family_cache_read[family] += cached
        family_models[family].add(model)
        model_key = (model or "codex/openai")[:48]
        model_tokens[model_key]["input"] += inp
        model_tokens[model_key]["output"] += out
        model_tokens[model_key]["cache_read"] += cached
        source_breakdown["codex"]["input_tokens"] += inp
        source_breakdown["codex"]["output_tokens"] += out
        source_breakdown["codex"]["cache_read_tokens"] += cached
        source_breakdown["codex"]["reasoning_tokens"] += reasoning
        source_breakdown["codex"]["billable_tokens"] += billable
        source_breakdown["codex"]["estimated_cost_usd"] += call_cost
        source_breakdown["codex"]["api_calls"] += 1

        if billable > 0:
            day = datetime.fromtimestamp(int(ev.get("timestamp") or time.time())).strftime("%Y-%m-%d")
            daily_tokens[day] += billable
            daily_cost[day] += call_cost
            session_tokens[_session_key("codex", ev.get("response_id", "unknown"))] += billable

    if CODEX_LOGS_DB.exists() and not codex_events:
        data_quality.append({
            "source": "codex",
            "status": "zero_tokens",
            "message": "Codex auth/logs are present, but no recent response usage rows were found in the local log DB.",
        })

    gemini_status = _gemini_local_status()
    source_breakdown["gemini_cli"]["sessions"] = gemini_status["sessions"]
    source_breakdown["gemini_cli"]["api_calls"] = 0
    if gemini_status["oauth_present"]:
        data_quality.append({
            "source": "gemini",
            "status": "manual",
            "message": "Gemini OAuth/history files are present, but local Gemini history does not expose token or dollar usage. Use imported Google/Gemini card charges for spend.",
        })
    else:
        data_quality.append({
            "source": "gemini",
            "status": "missing",
            "message": "No Gemini OAuth file found locally.",
        })

    hermes_rows = list(_iter_hermes_sessions(days=30) or [])
    if HERMES_STATE_DB.exists():
        source_breakdown["hermes"]["db_path"] = str(HERMES_STATE_DB)
        source_breakdown["hermes"]["sessions"] = len(hermes_rows)
    else:
        data_quality.append({
            "source": "hermes",
            "status": "missing",
            "message": f"Hermes state DB not found at {HERMES_STATE_DB}",
        })

    for row in hermes_rows:
        sid = row.get("id") or "unknown"
        model = row.get("model") or ""
        provider = row.get("billing_provider") or ""
        family = _classify_provider_model(provider, model)
        inp = int(row.get("input_tokens") or 0)
        out = int(row.get("output_tokens") or 0)
        cr = int(row.get("cache_read_tokens") or 0)
        cc = int(row.get("cache_write_tokens") or 0)
        reasoning = int(row.get("reasoning_tokens") or 0)
        billable = inp + out + cc
        actual_cost = float(row.get("actual_cost_usd") or 0.0)
        estimated_cost = float(row.get("estimated_cost_usd") or 0.0)
        cost_for_rollup = actual_cost or estimated_cost

        sessions_seen.add(_session_key("hermes", sid))
        family_input[family] += inp
        family_output[family] += out
        family_cache_read[family] += cr
        family_cache_create[family] += cc
        if model and (inp or out or cr or cc):
            family_models[family].add(model)
        if inp or out or cr or cc:
            model_key = model or provider or "hermes-unknown"
            if provider and provider not in model_key:
                model_key = f"{provider}/{model_key}"
            model_key = model_key[:48]
            model_tokens[model_key]["input"] += inp
            model_tokens[model_key]["output"] += out
            model_tokens[model_key]["cache_read"] += cr
            model_tokens[model_key]["cache_create"] += cc

        source_breakdown["hermes"]["input_tokens"] += inp
        source_breakdown["hermes"]["output_tokens"] += out
        source_breakdown["hermes"]["cache_read_tokens"] += cr
        source_breakdown["hermes"]["cache_creation_tokens"] += cc
        source_breakdown["hermes"]["reasoning_tokens"] += reasoning
        source_breakdown["hermes"]["billable_tokens"] += billable
        source_breakdown["hermes"]["actual_cost_usd"] += actual_cost
        source_breakdown["hermes"]["estimated_cost_usd"] += estimated_cost
        source_breakdown["hermes"]["api_calls"] += int(row.get("api_call_count") or 0)

        if billable > 0:
            started = float(row.get("started_at") or row.get("ended_at") or 0)
            if started:
                day = datetime.fromtimestamp(started).strftime("%Y-%m-%d")
                daily_tokens[day] += billable
                daily_cost[day] += cost_for_rollup
            session_tokens[_session_key("hermes", sid)] += billable

    if hermes_rows and source_breakdown["hermes"]["billable_tokens"] == 0:
        data_quality.append({
            "source": "hermes",
            "status": "zero_tokens",
            "message": (
                "Hermes state DB is readable, but all local Hermes sessions have 0 token counts. "
                "If live Hermes is only on Railway, mirror/export Railway /root/.hermes/state.db "
                "or expose /api/hermes-os/spend/series to make AIS-OS fully authoritative."
            ),
        })

    days_left = _days_left_in_cycle()
    rolling_window_days = 30

    # Five-hour window for Claude Pro Max
    five_h = _five_hour_window_stats()

    subs_out = []
    total_api_equiv = 0.0
    total_sub_usd = 0.0

    for sub in SUBSCRIPTIONS:
        family = sub["model_family"]
        inp = family_input[family]
        out = family_output[family]
        cr = family_cache_read[family]
        cc = family_cache_create[family]
        # Billable usage = input (non-cached) + output + cache_creation (billed as input)
        used_billable = inp + out + cc

        # API equivalent cost — per-model accurate pricing
        # Sum across every model bucket that belongs to this subscription family
        api_cost = 0.0
        sub_model_breakdown = []
        for model_key, tok in model_tokens.items():
            # Only count models that belong to this subscription's family
            model_family = _classify_model(model_key)
            if model_family != family:
                continue
            model_cost = compute_api_cost(
                input_tokens=tok["input"],
                output_tokens=tok["output"],
                cache_creation_tokens=tok["cache_create"],
                cache_read_tokens=tok["cache_read"],
                model_str=model_key,
            )
            api_cost += model_cost
            sub_model_breakdown.append({
                "model": model_key,
                "input_tokens": tok["input"],
                "output_tokens": tok["output"],
                "cache_read_tokens": tok["cache_read"],
                "cache_creation_tokens": tok["cache_create"],
                "equiv_usd": round(model_cost, 2),
            })
        # Sort breakdown by cost descending
        sub_model_breakdown.sort(key=lambda x: x["equiv_usd"], reverse=True)

        # If no per-model data for this family (e.g. openai/gemini with no jsonl events),
        # fall back to family-level totals with default rates
        if api_cost == 0.0 and used_billable > 0:
            models_seen = family_models.get(family, set())
            best_model = next(iter(sorted(models_seen, key=lambda m: "opus" in m, reverse=True)), "")
            rate = _get_rate_for_model(best_model, family)
            api_cost = (
                (inp / 1_000_000) * rate["input_per_1m"] +
                (out / 1_000_000) * rate["output_per_1m"] +
                (cc / 1_000_000) * rate["input_per_1m"] +
                (cr / 1_000_000) * rate["input_per_1m"] * 0.1
            )
        api_cost = round(api_cost, 2)
        if family == "claude" and source_breakdown["hermes"]["estimated_cost_usd"]:
            # Hermes has its own provider-aware estimator. Prefer it where
            # available so its non-Claude providers do not get forced through
            # AIS-OS's Claude-biased fallback table.
            api_cost = round(max(api_cost, source_breakdown["hermes"]["estimated_cost_usd"]), 2)
        total_api_equiv += api_cost

        sub_usd = sub["monthly_usd"]
        total_sub_usd += sub_usd

        plan = sub["plan_tokens"]
        if plan is not None and plan > 0:
            pct = round(min((used_billable / plan) * 100, 100), 1)
        else:
            pct = None  # No plan ceiling — rate-limited

        daily_rate = used_billable / rolling_window_days

        entry = {
            "name": sub["name"],
            "model_family": family,
            "monthly_usd": sub_usd,
            "plan_tokens": plan,
            "rate_limit_note": sub.get("rate_limit_note", ""),
            "used_tokens": used_billable,
            "input_tokens": inp,
            "output_tokens": out,
            "cache_read_tokens": cr,
            "cache_creation_tokens": cc,
            "pct": pct,
            "days_left": days_left,
            "daily_burn": round(daily_rate),
            "api_equivalent_usd": api_cost,
            "net_savings_usd": round(sub_usd - api_cost, 2),
            "model_breakdown": sub_model_breakdown,
        }

        # Claude Pro Max: attach 5h window stats
        if family == "claude":
            entry["window_5h"] = five_h

        # Non-Claude: mark as manual
        if family in ("openai", "gemini") and used_billable == 0:
            entry["manual_tracking"] = True

        subs_out.append(entry)

    total_tokens = sum(
        family_input[f["model_family"]] + family_output[f["model_family"]] + family_cache_create[f["model_family"]]
        for f in SUBSCRIPTIONS
    )
    total_api_equiv = round(total_api_equiv, 2)
    total_sub_usd = round(total_sub_usd, 2)
    total_actual_or_estimated_cost = round(
        total_api_equiv + max(0.0, source_breakdown["hermes"]["actual_cost_usd"] - source_breakdown["hermes"]["estimated_cost_usd"]),
        2,
    )

    # Per-model breakdown (top 10 by output)
    model_summary = sorted(
        [{"model": k, **v} for k, v in model_tokens.items()],
        key=lambda x: x["output"],
        reverse=True,
    )[:10]

    provider_accounts = {
        "openrouter": _fetch_openrouter_account_usage() or {"configured": False, "ok": False},
        "openai": _fetch_openai_account_usage(days=30),
    }
    key_inventory = _scan_key_inventory()
    card_spend = _build_ai_card_spend(days=30)
    subscription_by_provider = {
        "anthropic": float(os.environ.get("CLAUDE_MAX_MONTHLY_USD", "100")),
        "openai": float(os.environ.get("CHATGPT_MONTHLY_USD", "20")),
        "google_gemini": float(os.environ.get("GEMINI_MONTHLY_USD", "21.31")),
        "openrouter": 0.0,
    }
    source_tokens_by_provider = {
        "anthropic": source_breakdown["claude_code"]["billable_tokens"],
        "openai": source_breakdown["codex"]["billable_tokens"],
        "google_gemini": source_breakdown["gemini_cli"]["billable_tokens"],
        "openrouter": 0,
        "hermes": source_breakdown["hermes"]["billable_tokens"],
    }
    source_cost_by_provider = {
        "anthropic": source_breakdown["claude_code"]["estimated_cost_usd"],
        "openai": source_breakdown["codex"]["estimated_cost_usd"],
        "google_gemini": source_breakdown["gemini_cli"]["estimated_cost_usd"],
        "openrouter": 0.0,
        "hermes": source_breakdown["hermes"]["actual_cost_usd"] or source_breakdown["hermes"]["estimated_cost_usd"],
    }
    provider_labels = {
        "anthropic": "Claude / Anthropic",
        "openai": "ChatGPT / Codex / OpenAI",
        "google_gemini": "Gemini / Google AI",
        "openrouter": "OpenRouter",
        "hermes": "Hermes",
    }
    provider_rows = []
    all_providers = sorted(set(provider_labels) | set(card_spend["by_provider"]) | set(subscription_by_provider))
    for provider in all_providers:
        account = provider_accounts.get(provider) or {}
        account_spend = 0.0
        if provider == "openrouter" and account.get("ok"):
            account_spend = _safe_float(account.get("usage_monthly_usd") or account.get("key_usage_usd") or 0.0)
        if provider == "openai" and account.get("ok"):
            account_spend = _safe_float(account.get("total_cost_usd"))
        provider_subscription = round(subscription_by_provider.get(provider, 0.0), 2)
        provider_card = round(card_spend["by_provider"].get(provider, 0.0), 2)
        provider_known_cash = provider_subscription
        if provider in {"anthropic", "openrouter", "openai"}:
            provider_known_cash += max(provider_card, account_spend)
        elif provider not in subscription_by_provider:
            provider_known_cash += provider_card
        provider_rows.append({
            "provider": provider,
            "label": provider_labels.get(provider, provider),
            "known_cash_usd": round(provider_known_cash, 2),
            "subscription_usd": provider_subscription,
            "card_charges_usd": provider_card,
            "account_usage_usd": round(account_spend, 4),
            "account_ok": bool(account.get("ok")),
            "account_error": account.get("message") or account.get("error") or "",
            "local_tokens": int(source_tokens_by_provider.get(provider, 0) or 0),
            "local_estimated_cost_usd": round(source_cost_by_provider.get(provider, 0.0) or 0.0, 4),
            "status": "tracked" if (
                card_spend["by_provider"].get(provider)
                or subscription_by_provider.get(provider)
                or source_tokens_by_provider.get(provider)
                or account_spend
            ) else "gap",
        })
    actual_subscription_usd = round(sum(subscription_by_provider.values()), 2)
    # This is a practical "cash I know about" number: configured subscriptions
    # plus imported provider top-ups/API charges. Google/Gemini is already in
    # the subscription bucket, so do not double-count the same card charge.
    actual_known_usd = round(
        actual_subscription_usd
        + card_spend["by_provider"].get("anthropic", 0.0)
        + max(card_spend["by_provider"].get("openrouter", 0.0), _safe_float(provider_accounts["openrouter"].get("usage_monthly_usd") or provider_accounts["openrouter"].get("key_usage_usd") or 0.0))
        + max(card_spend["by_provider"].get("openai", 0.0), _safe_float(provider_accounts["openai"].get("total_cost_usd"))),
        2,
    )
    actual_spend = {
        "known_monthly_usd": actual_known_usd,
        "subscription_usd": actual_subscription_usd,
        "imported_api_charges_usd": round(
            card_spend["by_provider"].get("anthropic", 0.0)
            + max(card_spend["by_provider"].get("openrouter", 0.0), _safe_float(provider_accounts["openrouter"].get("usage_monthly_usd") or provider_accounts["openrouter"].get("key_usage_usd") or 0.0))
            + max(card_spend["by_provider"].get("openai", 0.0), _safe_float(provider_accounts["openai"].get("total_cost_usd"))),
            2,
        ),
        "card_window": card_spend,
        "daily_card_spend": _build_daily_card_spend(card_spend),
        "providers": provider_rows,
        "note": "Cash spend is subscriptions you configured plus imported Apple Card AI API/top-up charges. API-equivalent token value is separate and is not money charged by Claude Max/ChatGPT Plus.",
    }

    return {
        "subscriptions": subs_out,
        "total_tokens_30d": total_tokens,
        "total_sessions_30d": len(sessions_seen),
        "total_subscription_usd": total_sub_usd,
        "total_api_equivalent_usd": total_api_equiv,
        "net_savings_usd": round(total_sub_usd - total_api_equiv, 2),
        "daily_burn_14d": _build_daily_burn(daily_tokens, days=14),
        "top_sessions": _per_session_top(session_tokens, top_n=10),
        "per_model_breakdown": model_summary,
        "source_breakdown": {
            key: {
                **value,
                "estimated_cost_usd": round(value.get("estimated_cost_usd", 0.0), 4),
                "actual_cost_usd": round(value.get("actual_cost_usd", 0.0), 4),
            }
            for key, value in source_breakdown.items()
        },
        "provider_accounts": provider_accounts,
        "key_inventory": key_inventory,
        "actual_spend": actual_spend,
        "budget_status": _build_budget_status(total_tokens, total_actual_or_estimated_cost, daily_tokens, daily_cost),
        "data_quality": data_quality,
        "limit_guidance": [
            "Set AIOS_DAILY_TOKEN_LIMIT / AIOS_MONTHLY_TOKEN_LIMIT for dashboard alerts.",
            "Set AIOS_DAILY_COST_LIMIT_USD / AIOS_MONTHLY_COST_LIMIT_USD for spend alerts.",
            "For Hermes hard caps, lower model.max_tokens and agent.max_turns in Hermes config.yaml; provider-side account limits are the true spend stop.",
        ],
        "generated_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import sys
    print("Running usage_stats() dry-run...")
    try:
        result = usage_stats()
        print(f"OK — {result['total_sessions_30d']} sessions, {result['total_tokens_30d']:,} billable tokens (30d)")
        for s in result["subscriptions"]:
            pct_str = f"{s['pct']}%" if s['pct'] is not None else "rate-limited"
            note = f" [{s.get('rate_limit_note','')}]" if s.get('rate_limit_note') else ""
            print(f"  {s['name']}: {s['used_tokens']:,} billable tokens ({pct_str}){note}")
            print(f"    in={s['input_tokens']:,}  out={s['output_tokens']:,}  cache_read={s['cache_read_tokens']:,}  cache_create={s['cache_creation_tokens']:,}")
            if s.get('window_5h'):
                w = s['window_5h']
                print(f"    5h window: {w['total_tokens']:,} tokens ({w['events']} events)")
            print(f"    API equiv: ${s['api_equivalent_usd']}")
        print(f"Total sub: ${result['total_subscription_usd']} | API equiv: ${result['total_api_equivalent_usd']} | savings: ${result['net_savings_usd']}")
        print("\nPer-model breakdown:")
        for m in result['per_model_breakdown'][:5]:
            print(f"  {m['model']}: in={m['input']:,} out={m['output']:,} cache_read={m['cache_read']:,}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)
