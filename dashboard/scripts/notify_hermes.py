"""Push Telegram messages via Hermes bot token."""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
LOG = DATA / "notify_log.json"

# Env file search order — first hit wins
_ENV_CANDIDATES = [
    Path("/Volumes/Samsung PSSD T7/hermes-claw/.env"),   # primary (new name)
    Path("/Volumes/Samsung PSSD T7/gravity-claw/.env"),   # legacy name fallback
    BASE.parent / ".env",                                  # AIS-OS root .env
    Path.home() / ".env",                                  # home fallback
]


def _load_env() -> dict:
    """Read first available .env, return key→value dict. Safe parser, skips bad lines."""
    env = {}
    for candidate in _ENV_CANDIDATES:
        if not candidate.exists():
            continue
        for line in candidate.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            if " " in k or not k:
                continue  # skip "Supabase URL=..." style lines
            env[k] = v.strip().strip('"').strip("'")
        if env:
            break  # stop at first file that yields keys
    # Also honour live environment variables (override file values)
    for key in ("TELEGRAM_BOT_TOKEN", "ALLOWED_USER_IDS", "TELEGRAM_CHAT_ID"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def _log() -> dict:
    if LOG.exists():
        try:
            return json.loads(LOG.read_text())
        except Exception:
            pass
    return {"sent": []}


def _save_log(d: dict):
    try:
        LOG.write_text(json.dumps(d, indent=2))
    except Exception:
        pass


def post(message: str, event_id: str | None = None) -> dict:
    """Send Telegram message. If event_id given, dedupe via notify_log.json."""
    if event_id:
        log = _log()
        if event_id in {e["id"] for e in log["sent"]}:
            return {"ok": True, "skipped": "duplicate", "event_id": event_id}

    env = _load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    # Support both ALLOWED_USER_IDS (Hermes style) and TELEGRAM_CHAT_ID
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("ALLOWED_USER_IDS", "").split(",")[0].strip()

    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not found in any .env file"}
    if not chat_id:
        return {"ok": False, "error": "No chat_id — set TELEGRAM_CHAT_ID or ALLOWED_USER_IDS"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if event_id and resp.get("ok"):
        log = _log()
        log["sent"].append({"id": event_id, "ts": time.time(), "msg": message[:80]})
        log["sent"] = log["sent"][-500:]
        _save_log(log)

    return resp


def debug_env() -> dict:
    """Return env source info for diagnostics (no secret values)."""
    env = _load_env()
    return {
        "token_found": bool(env.get("TELEGRAM_BOT_TOKEN")),
        "chat_id_found": bool(env.get("TELEGRAM_CHAT_ID") or env.get("ALLOWED_USER_IDS")),
        "sources_checked": [str(p) for p in _ENV_CANDIDATES],
        "source_exists": [str(p) for p in _ENV_CANDIDATES if p.exists()],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        print(json.dumps(debug_env(), indent=2))
    else:
        msg = sys.argv[1] if len(sys.argv) > 1 else "AIOS bridge test"
        print(json.dumps(post(msg), indent=2))
