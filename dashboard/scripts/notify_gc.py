"""Push Telegram messages via Gravity Claw's bot token."""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
GC_ENV = Path("/Volumes/Samsung PSSD T7/gravity-claw/.env")
LOG = DATA / "notify_log.json"


def _gc_env() -> dict:
    env = {}
    if not GC_ENV.exists():
        return env
    for line in GC_ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _log() -> dict:
    if LOG.exists():
        return json.loads(LOG.read_text())
    return {"sent": []}


def _save_log(d: dict):
    LOG.write_text(json.dumps(d, indent=2))


def post(message: str, event_id: str | None = None) -> dict:
    """Send Telegram message. If event_id given, dedupe via notify_log.json."""
    if event_id:
        log = _log()
        if event_id in {e["id"] for e in log["sent"]}:
            return {"ok": True, "skipped": "duplicate", "event_id": event_id}

    env = _gc_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("ALLOWED_USER_IDS", "").split(",")[0].strip()
    if not (token and chat_id):
        return {"ok": False, "error": "missing TELEGRAM_BOT_TOKEN or ALLOWED_USER_IDS"}

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
        log["sent"] = log["sent"][-500:]  # cap
        _save_log(log)

    return resp


if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "AIOS bridge test"
    print(json.dumps(post(msg), indent=2))
