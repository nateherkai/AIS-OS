import os
import json
import secrets
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

load_dotenv()

# Paths
BASE = Path(__file__).parent
DATA = BASE / "data"
SCRIPTS = BASE / "scripts"
ROOT = BASE.parent  # AIS-OS root (one level up from dashboard/)

import sys
sys.path.insert(0, str(SCRIPTS))
from supabase_client import get_schools, get_pipeline_summary
from parse_apple_card import parse_and_update, find_all_csvs
from pillars import build_pillars
from memory_feed import build_feed as build_memory_feed
from memory_graph import build as build_memory_graph
from roi import compute as compute_roi
from pricing import tier_monthly_usd, TIER_MONTHLY_DEFAULT, is_recognized_tier
import bridge as bridge_mod
import notify_hermes
try:
    import gmail_client
except ImportError:
    gmail_client = None
from wizard_detect import detect_all, save_wizard
from supabase_widget import (
    status as sb_status,
    list_tables as sb_tables,
    preview_table as sb_preview,
    advisors as sb_advisors,
)
from pinecone_widget import stats as pc_stats, recent as pc_recent, query as pc_query
from usage_tracker import usage_stats
import personal_agent as agent_mod
import wiki_reader as wiki_mod

# Ensure BRIDGE_TOKEN exists (generate once, persist to .env)
if not os.environ.get("BRIDGE_TOKEN"):
    env_file = BASE.parent / ".env"
    tok = secrets.token_urlsafe(24)
    os.environ["BRIDGE_TOKEN"] = tok
    try:
        with open(env_file, "a") as f:
            f.write(f"\nBRIDGE_TOKEN={tok}\n")
    except Exception:
        pass

app = FastAPI(title="Ag Coach Pro AIOS Dashboard")

# F10: CSRF Origin check middleware — blocks cross-origin POST/PUT/PATCH/DELETE
# Bridge endpoints (/api/bridge/) are exempt: they use X-Bridge-Token auth instead.
class OriginCheckMiddleware(BaseHTTPMiddleware):
    _ALLOWED = ("http://localhost:8080", "http://127.0.0.1:8080")

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path
            # Exempt bridge endpoints (token-authenticated) and local-test (loopback-gated)
            if not path.startswith("/api/bridge/"):
                origin = request.headers.get("origin") or request.headers.get("referer", "")
                if origin and not any(origin.startswith(a) for a in self._ALLOWED):
                    return JSONResponse({"error": "Cross-origin request denied"}, status_code=403)
        return await call_next(request)

app.add_middleware(OriginCheckMiddleware)

# ── Data helpers ──────────────────────────────────────────────

def read_json(name: str) -> dict:
    with open(DATA / name) as f:
        return json.load(f)

def write_json(name: str, data: dict):
    with open(DATA / name, "w") as f:
        json.dump(data, f, indent=2)

# ── Revenue helpers ───────────────────────────────────────────

def compute_monthly_revenue(paid_schools: list) -> dict:
    """Sum actual monthly revenue across paid schools using per-tier pricing.

    Each school should have a 'subscription_tier' field from Supabase.
    Falls back to TIER_MONTHLY_DEFAULT ($124.58, Lone Star Elite) if missing or unrecognized.
    Returns total, per-school breakdown, and warning if any tier is unrecognized.
    """
    total = 0.0
    breakdown = []
    tier_fallback_used = False
    unrecognized_tiers = set()
    for s in paid_schools:
        tier = s.get("subscription_tier") or ""
        if not tier:
            monthly = TIER_MONTHLY_DEFAULT
            tier_fallback_used = True
        elif not is_recognized_tier(tier):
            # Tier value exists but isn't a known tier name — use default, flag it
            monthly = tier_monthly_usd(tier)  # pricing.py handles via _default
            tier_fallback_used = True
            unrecognized_tiers.add(tier)
        else:
            monthly = tier_monthly_usd(tier)
        total += monthly
        breakdown.append({
            "name": s.get("name", ""),
            "tier": tier or "unknown",
            "monthly_usd": monthly,
        })
    result = {
        "total": round(total, 2),
        "breakdown": breakdown,
        "tier_fallback_used": tier_fallback_used,
    }
    if unrecognized_tiers:
        result["revenue_warning"] = (
            f"Unrecognized tier(s) in Supabase: {sorted(unrecognized_tiers)} — "
            f"defaulting to Lone Star Elite (${TIER_MONTHLY_DEFAULT:.2f}/mo). "
            "Update pricing.py TIER_PRICES to add these tier keys."
        )
    return result


# ── Routes ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(BASE / "index.html")

@app.get("/api/pipeline")
def pipeline():
    try:
        schools = get_schools()
        summary = get_pipeline_summary(schools)
        # Add days_in_trial for each trial school
        for s in summary["trials"]:
            created = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
            s["days_in_trial"] = (datetime.now().astimezone() - created).days
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses")
def expenses():
    data = read_json("expenses.json")
    total = sum(e["amount"] for e in data["expenses"])
    return {"expenses": data["expenses"], "total": total, "last_updated": data.get("last_updated")}

@app.post("/api/expenses/sync")
def sync_expenses():
    result = parse_and_update()
    return result

@app.get("/api/burn")
def api_burn():
    """Real card burn — full monthly spend, AI subset, categories, trends."""
    data = read_json("expenses.json")
    return {
        "monthly_full": data.get("monthly_charges_full", 0),
        "monthly_curated_ai": data.get("monthly_charges_curated", 0),
        "monthly_avg_full": data.get("monthly_avg_full", 0),
        "monthly_interest": data.get("monthly_interest", 0),
        "top_vendors": data.get("top_vendors_30d", []),
        "by_category": data.get("by_category_30d", {}),
        "period_summaries": data.get("period_summaries", []),
        "last_csv_date": data.get("last_csv_date"),
        "last_updated": data.get("last_updated"),
    }

@app.get("/api/burn/by-business")
def api_burn_by_business():
    """Business-attributed burn: 30d totals, 4-mo avg, per-period breakdown, unmapped vendors."""
    data = read_json("expenses.json")
    attr = read_json("vendor_attribution.json")
    return {
        "buckets": attr.get("buckets", []),
        "by_business_30d": data.get("by_business_30d", {}),
        "by_business_4mo_avg": data.get("by_business_4mo_avg", {}),
        "period_summaries_business": [
            {"month": p["month"], "month_name": p.get("month_name", p["month"]),
             "by_business": p.get("by_business", {}), "total": p["full"]}
            for p in data.get("period_summaries", [])
        ],
        "unmapped_vendors": data.get("unmapped_vendors", []),
        "top_vendors_30d": data.get("top_vendors_30d", []),
    }

@app.post("/api/burn/refresh")
def api_burn_refresh():
    """Manually trigger Apple Card CSV reimport (idempotent)."""
    res = subprocess.run(
        ["python3", str(SCRIPTS / "auto_import_card.py")],
        capture_output=True, text=True, timeout=30,
    )
    return {"ok": res.returncode == 0, "stdout": res.stdout[-500:], "stderr": res.stderr[-300:]}

@app.get("/api/kpis")
def kpis():
    schools = get_schools()
    summary = get_pipeline_summary(schools)
    expenses = read_json("expenses.json")
    debt = read_json("debt.json")
    # R3c: curated AI/dev burn only — full card total shown separately in finances
    total_burn = expenses.get("monthly_charges_curated") or sum(e["amount"] for e in expenses["expenses"])
    rev = compute_monthly_revenue(summary["paid"])
    monthly_revenue = rev["total"]
    net = monthly_revenue - total_burn
    return {
        "monthly_revenue": monthly_revenue,
        "monthly_burn": round(total_burn, 2),
        "net": round(net, 2),
        "paid_schools": summary["paid_count"],
        "trial_schools": summary["trial_count"],
        "school_goal": 50,
        "debt_total_paid": debt["total_paid"],
        "debt_goal": debt["goal"],
        "revenue_breakdown": rev["breakdown"],
        "tier_fallback_used": rev["tier_fallback_used"],
        "burn_by_business": expenses.get("by_business_30d", {}),
        **({"revenue_warning": rev["revenue_warning"]} if rev.get("revenue_warning") else {}),
    }

# ── Tasks ─────────────────────────────────────────────────────

class TaskUpdate(BaseModel):
    id: int
    done: bool

class TaskAdd(BaseModel):
    text: str
    tag: str = "General"

@app.get("/api/tasks")
def get_tasks():
    return read_json("tasks.json")

@app.post("/api/tasks/update")
def update_task(update: TaskUpdate):
    data = read_json("tasks.json")
    for t in data["tasks"]:
        if t["id"] == update.id:
            t["done"] = update.done
    write_json("tasks.json", data)
    return {"ok": True}

@app.post("/api/tasks/add")
def add_task(task: TaskAdd):
    data = read_json("tasks.json")
    new_id = max((t["id"] for t in data["tasks"]), default=0) + 1
    data["tasks"].append({"id": new_id, "text": task.text, "tag": task.tag, "done": False})
    write_json("tasks.json", data)
    return {"id": new_id}

# ── Debt ──────────────────────────────────────────────────────

class DebtPayment(BaseModel):
    amount: float
    note: str = ""

@app.get("/api/debt")
def get_debt():
    return read_json("debt.json")

@app.post("/api/debt/log")
def log_debt(payment: DebtPayment):
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    data = read_json("debt.json")
    data["payments"].append({
        "date": datetime.now().isoformat(),
        "amount": payment.amount,
        "note": payment.note,
    })
    data["total_paid"] = round(data["total_paid"] + payment.amount, 2)
    write_json("debt.json", data)
    return {"total_paid": data["total_paid"]}

# ── Pipeline check skill ───────────────────────────────────────

@app.get("/api/skills/pipeline-check")
def pipeline_check():
    schools = get_schools()
    summary = get_pipeline_summary(schools)
    expenses = read_json("expenses.json")
    total_burn = expenses.get("monthly_charges_curated") or sum(e["amount"] for e in expenses["expenses"])
    rev = compute_monthly_revenue(summary["paid"])
    monthly_revenue = rev["total"]
    net = monthly_revenue - total_burn

    for s in summary["trials"]:
        created = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
        s["days_in_trial"] = (datetime.now().astimezone() - created).days

    cold = [s for s in summary["trials"] if s.get("days_in_trial", 0) >= 14]

    lines = [
        f"=== Pipeline Check — {datetime.now().strftime('%Y-%m-%d')} ===",
        "",
        f"GOAL: {summary['school_goal']} paid schools by {summary['goal_date']}",
        f"Paid:    {summary['paid_count']} / {summary['school_goal']}  ({summary['paid_count']/summary['school_goal']*100:.0f}% to goal)",
        f"Trials:  {summary['trial_count']}",
        f"Gap:     {summary['school_goal'] - summary['paid_count']} schools to close",
        "",
        "REVENUE",
        f"MRR: ${monthly_revenue:.2f}  |  Burn (AI/dev): ${total_burn:.2f}  |  Net: ${net:.2f}",
        "",
        "TRIALS GOING COLD (>14 days)",
    ]
    if cold:
        for s in cold:
            lines.append(f"→ {s['name']} — {s.get('advisor_name','')} ({s.get('days_in_trial',0)}d)")
    else:
        lines.append("→ None — all under 14 days")

    if summary["trial_count"] > 0:
        oldest = max(summary["trials"], key=lambda s: s.get("days_in_trial", 0))
        lines += ["", f"ACTION: Follow up with {oldest['name']} ({oldest.get('days_in_trial',0)}d in trial)"]
    elif summary["paid_count"] < 10:
        lines += ["", "ACTION: No active trials — send a new MailerLite blast"]

    return {"output": "\n".join(lines)}

# ── Six Pillars / Memory / ROI / Dreams ───────────────────────

@app.get("/api/pillars")
def api_pillars():
    return build_pillars()

@app.get("/api/memory-feed")
def api_memory_feed(limit: int = 30):
    return build_memory_feed(limit=limit)

@app.get("/api/memory-graph")
def api_memory_graph():
    return build_memory_graph()

@app.get("/api/roi")
def api_roi():
    return compute_roi()

@app.get("/api/dreams")
def api_dreams(date: str | None = None):
    dreams_dir = DATA / "dreams"
    if not dreams_dir.exists():
        return {"items": []}
    if date:
        f = dreams_dir / f"{date}.json"
        if not f.exists():
            raise HTTPException(404, f"No dream for {date}")
        return json.loads(f.read_text())
    files = sorted(dreams_dir.glob("*.json"), reverse=True)
    if not files:
        return {"items": [], "message": "No dreams yet — run scripts/dream_machine.py"}
    return json.loads(files[0].read_text())

class DreamAction(BaseModel):
    dream_id: str | None = None
    headline: str | None = None
    action: str
    date: str | None = None

def _dream_file(date: str | None = None) -> Path:
    dreams_dir = DATA / "dreams"
    if date:
        return dreams_dir / f"{date}.json"
    files = sorted(dreams_dir.glob("*.json"), reverse=True)
    if not files:
        raise HTTPException(404, "No dream files found")
    return files[0]

def _find_dream_card(dream: dict, body: DreamAction):
    cards = dream.setdefault("cards", [])
    target_id = body.dream_id
    target_headline = body.headline
    for card in cards:
        if target_id and str(card.get("id")) == str(target_id):
            return card
        if target_headline and card.get("title") == target_headline:
            return card
    if target_headline:
        card = {
            "id": target_id or f"d{len(cards) + 1}",
            "dim": "manual",
            "title": target_headline,
            "insight": target_headline,
            "action": "Review and decide",
            "estimated_value_minutes": 30,
            "status": "open",
        }
        cards.append(card)
        return card
    raise HTTPException(404, "Dream card not found")

@app.post("/api/dreams/action")
def api_dreams_action(body: DreamAction):
    """Accept, dismiss, complete, or convert a dream card into a task."""
    action = body.action.lower().strip()
    if action not in {"accept", "dismiss", "complete", "task"}:
        raise HTTPException(400, "action must be accept, dismiss, complete, or task")
    f = _dream_file(body.date)
    dream = json.loads(f.read_text())
    card = _find_dream_card(dream, body)
    status_map = {
        "accept": "accepted",
        "dismiss": "dismissed",
        "complete": "completed",
        "task": "accepted",
    }
    card["status"] = status_map[action]
    card["updated_at"] = datetime.now().isoformat()
    # Dismiss → snooze headline so dream_machine won't resurface it
    if action == "dismiss":
        headline = card.get("insight") or card.get("title", "")
        cfg_path = BASE / "config.json"
        if headline and cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text())
                snoozed = cfg.get("snoozed_dream_headlines", [])
                if headline not in snoozed:
                    snoozed.append(headline)
                    cfg["snoozed_dream_headlines"] = snoozed[-200:]
                    cfg_path.write_text(json.dumps(cfg, indent=2))
            except Exception:
                pass
    task_id = None
    if action == "task":
        tasks = read_json("tasks.json")
        task_id = max((t["id"] for t in tasks["tasks"]), default=0) + 1
        tasks["tasks"].append({
            "id": task_id,
            "text": f"Dream: {card.get('title', 'Untitled recommendation')}",
            "tag": "AIOS",
            "done": False,
        })
        write_json("tasks.json", tasks)
        card["task_id"] = task_id
    f.write_text(json.dumps(dream, indent=2))
    _invalidate_search_cache()
    return {"ok": True, "status": card["status"], "task_id": task_id, "card": card}

@app.post("/api/dreams/run")
def api_dreams_run():
    res = subprocess.run(
        ["python3", str(SCRIPTS / "dream_machine.py")],
        capture_output=True, text=True, timeout=60,
    )
    return {"ok": res.returncode == 0, "stdout": res.stdout[-2000:], "stderr": res.stderr[-1000:]}

@app.post("/api/dreams/regenerate")
def api_dreams_regenerate():
    """Regenerate dream report by re-running dream_machine.py. Timeout 60s."""
    _invalidate_search_cache()  # F13: new dream data may change graph nodes
    try:
        res = subprocess.run(
            ["python3", str(SCRIPTS / "dream_machine.py")],
            capture_output=True, text=True, timeout=60,
        )
        result = {"ok": res.returncode == 0, "stdout": res.stdout[-2000:], "stderr": res.stderr[-1000:]}
        # F14: surface image_errors from regenerated dream file
        try:
            import json as _json
            dreams_dir = DATA / "dreams"
            files = sorted(dreams_dir.glob("*.json"), reverse=True)
            if files:
                dream = _json.loads(files[0].read_text())
                result["image_errors"] = dream.get("image_errors", [])
        except Exception:
            pass
        return result
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Dream regeneration timed out (60s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/lint/recompute")
def api_lint_recompute():
    """Recompute lint report by running scripts/lint.py. Timeout 60s."""
    lint_script = ROOT / "scripts" / "lint.py"
    if not lint_script.exists():
        return {"ok": False, "error": f"scripts/lint.py not found (looked at {lint_script})"}
    try:
        res = subprocess.run(
            ["python3", str(lint_script)],
            capture_output=True, text=True, timeout=60,
        )
        return {"ok": res.returncode == 0, "stdout": res.stdout[-2000:], "stderr": res.stderr[-1000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Lint recompute timed out (60s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

_FREQ_CRON = {
    "AM": "0 6 * * *",
    "PM": "0 22 * * *",
    "both": "0 6,22 * * *",
    "disabled": None,
}

@app.post("/api/dreams/schedule")
def api_dreams_schedule():
    """Return recommended cron entry from dream_prefs.frequency. No auto-install."""
    try:
        cfg_path = BASE / "config.json"
        cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
        freq = cfg.get("dream_prefs", {}).get("frequency", "PM")
        suggested = _FREQ_CRON.get(freq)
        return {
            "frequency": freq,
            "suggested_cron": suggested,
            "current_cron": cfg.get("dream_cron"),
            "note": "Run `crontab -e` and add the suggested line with the full path to dream_machine.py to install.",
        }
    except Exception as e:
        raise HTTPException(500, str(e))

class CronApply(BaseModel):
    cron: str | None = None

@app.post("/api/dreams/schedule/apply")
def api_dreams_schedule_apply(body: CronApply):
    """Write dream_cron into config.json (user still must `crontab -e` manually)."""
    _invalidate_search_cache()  # F13: config change may affect index
    try:
        cfg_path = BASE / "config.json"
        cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
        cfg["dream_cron"] = body.cron
        cfg_path.write_text(json.dumps(cfg, indent=2))
        return {"ok": True, "dream_cron": body.cron}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Bridge (Hermes two-way) ─────────────────────────────

class BridgeQuery(BaseModel):
    q: str | None = None
    scope: list[str] | None = None

class BridgePush(BaseModel):
    message: str
    event_id: str | None = None

class NotebookLMRun(BaseModel):
    args: list[str]

@app.get("/api/bridge/handshake")
def api_bridge_handshake():
    return bridge_mod.handshake()

@app.post("/api/bridge/query")
async def api_bridge_query(req: Request, body: BridgeQuery):
    expected = os.environ.get("BRIDGE_TOKEN", "")
    token = req.headers.get("x-bridge-token", "")
    if not expected or token != expected:
        raise HTTPException(401, "invalid X-Bridge-Token")
    return bridge_mod.snapshot(body.scope)

@app.post("/api/bridge/push")
async def api_bridge_push(req: Request, body: BridgePush):
    expected = os.environ.get("BRIDGE_TOKEN", "")
    token = req.headers.get("x-bridge-token", "")
    if not expected or token != expected:
        raise HTTPException(401, "invalid X-Bridge-Token")
    return notify_hermes.post(body.message, body.event_id)

@app.post("/api/bridge/local-test")
async def api_bridge_local_test(req: Request):
    """Loopback-only smoke test — sends a Telegram message via GC bot."""
    if req.client.host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(403, "loopback only")
    return notify_hermes.post(f"✅ AIOS bridge online — UI test {datetime.now().strftime('%H:%M:%S')}")

# ── NotebookLM Bridge ─────────────────────────────────────────

_NLM_BLOCKED = {"delete"}
_NLM_BIN = Path.home() / "bin" / "notebooklm"

@app.post("/api/bridge/notebooklm/run")
async def api_bridge_notebooklm_run(req: Request, body: NotebookLMRun):
    expected = os.environ.get("BRIDGE_TOKEN", "")
    token = req.headers.get("x-bridge-token", "")
    if not expected or token != expected:
        raise HTTPException(401, "invalid X-Bridge-Token")
    if not body.args:
        raise HTTPException(400, "args required")
    subcommand = body.args[0]
    if subcommand in _NLM_BLOCKED:
        raise HTTPException(403, f"'{subcommand}' blocked — run locally")
    nlm = str(_NLM_BIN) if _NLM_BIN.exists() else "notebooklm"
    result = subprocess.run(
        [nlm, *body.args],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "HOME": str(Path.home())},
    )
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

# ── Gmail Inbox ──────────────────────────────────────────────

@app.get("/api/inbox/status")
def api_inbox_status():
    if not gmail_client:
        return {"ready": False, "error": "gmail_client module not loaded"}
    return gmail_client.auth_status()

@app.post("/api/inbox/authorize")
def api_inbox_authorize():
    if not gmail_client:
        raise HTTPException(500, "gmail_client missing")
    return gmail_client.authorize()

@app.get("/api/inbox")
def api_inbox(q: str = "in:inbox", limit: int = 20):
    if not gmail_client:
        raise HTTPException(500, "gmail_client missing")
    try:
        return gmail_client.list_threads(q, limit)
    except Exception as e:
        raise HTTPException(500, f"Gmail error: {e}")

@app.get("/api/inbox/thread/{thread_id}")
def api_inbox_thread(thread_id: str):
    if not gmail_client:
        raise HTTPException(500, "gmail_client missing")
    return gmail_client.get_thread(thread_id)

class DraftBody(BaseModel):
    to: str
    subject: str
    body: str

@app.post("/api/inbox/draft")
def api_inbox_draft(d: DraftBody):
    if not gmail_client:
        raise HTTPException(500, "gmail_client missing")
    return gmail_client.send_draft(d.to, d.subject, d.body)

@app.get("/bridge/install.md")
def serve_install_md():
    p = BASE / "bridge" / "install.md"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="text/markdown")

# ── Wizard ────────────────────────────────────────────────────

@app.get("/api/wizard/detect")
def api_wizard_detect():
    try:
        return detect_all()
    except Exception as e:
        raise HTTPException(500, str(e))

class WizardSave(BaseModel):
    models: list = []
    storage: list = []
    memory: dict = {}
    hourly_value: float | None = None
    dream_prefs: dict = {}

@app.post("/api/wizard/save")
def api_wizard_save(body: WizardSave):
    _invalidate_search_cache()  # F13: wizard config change may affect graph/index
    try:
        return save_wizard(body.model_dump(), BASE / "config.json")
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Supabase ──────────────────────────────────────────────────

@app.get("/api/supabase/status")
def api_supabase_status():
    try:
        return sb_status()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/supabase/tables")
def api_supabase_tables():
    try:
        return {"tables": sb_tables()}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/supabase/table/{name}")
def api_supabase_table(name: str, limit: int = 20):
    try:
        return sb_preview(name, limit)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/supabase/advisors")
def api_supabase_advisors():
    return {"advisors": sb_advisors()}

# ── Hermes ─────────────────────────────────────────────

@app.get("/api/hermes/vault-status")
def api_gc_status():
    """Return Hermes vault connection status and recent memory files."""
    from pathlib import Path
    import os
    GC = Path("/Volumes/Samsung PSSD T7/hermes-claw")
    if not GC.exists():
        return {"connected": False, "error": "Vault not mounted"}
    mem = GC / "memory"
    mem_files = []
    total_count = 0
    try:
        for sub in sorted(mem.iterdir()):
            if not sub.is_dir():
                continue
            for f in sorted(sub.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                total_count += 1
                mem_files.append({
                    "path": str(f.relative_to(GC)),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()[:16],
                })
    except Exception as e:
        return {"connected": True, "error": str(e)}
    # Railway status — check for deploy config
    railway_toml = GC / "railway.toml"
    deploy_info = "railway.toml found" if railway_toml.exists() else "no railway.toml"
    try:
        pinecone = pc_stats()
    except Exception:
        pinecone = {}
    return {
        "connected": True,
        "vault_path": str(GC),
        "memory_files_sampled": len(mem_files),
        "memory_files": mem_files[:12],
        "deploy": deploy_info,
        "pinecone_vectors": pinecone.get("total_vectors"),
        "pinecone_index": pinecone.get("index", "gravityclaw-vector"),
        "pinecone_namespace": pinecone.get("namespace", "knowledge"),
    }

# ── Pinecone ──────────────────────────────────────────────────

@app.get("/api/pinecone/stats")
def api_pinecone_stats():
    try:
        return pc_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/pinecone/recent")
def api_pinecone_recent(limit: int = 50):
    try:
        return pc_recent(limit)
    except Exception as e:
        raise HTTPException(500, str(e))

class PineconeQuery(BaseModel):
    text: str
    top_k: int = 10

@app.post("/api/pinecone/query")
def api_pinecone_query(body: PineconeQuery):
    try:
        return pc_query(body.text, body.top_k)
    except Exception as e:
        return {"matches": [], "error": str(e)}

# ── Usage Tracking ────────────────────────────────────────────

@app.get("/api/usage")
def api_usage():
    try:
        return usage_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Personal Agent ─────────────────────────────────────────────

class AgentAsk(BaseModel):
    question: str
    mode: str = "full"

@app.post("/api/agent/ask")
def api_agent_ask(body: AgentAsk):
    try:
        return agent_mod.ask(body.question, body.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Wiki Browser (N2) ────────────────────────────────────────

import time as _time
_search_index_cache: dict = {"ts": 0, "data": None}

def _invalidate_search_cache():
    """F13: Clear server-side search index cache on any mutating write."""
    _search_index_cache["data"] = None
    _search_index_cache["ts"] = 0

@app.get("/api/wiki/tree")
def api_wiki_tree():
    try:
        return wiki_mod.tree()
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/wiki/page")
def api_wiki_page(path: str):
    if ".." in path:
        raise HTTPException(400, "Path traversal rejected")
    try:
        return wiki_mod.page(path)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/wiki/search")
def api_wiki_search(q: str = ""):
    if not q:
        return []
    try:
        return wiki_mod.search(q)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/search/index")
def api_search_index():
    """Return flat search index for Cmd+K palette. Cached 60s."""
    global _search_index_cache
    now = _time.time()
    if _search_index_cache["data"] and now - _search_index_cache["ts"] < 60:
        return _search_index_cache["data"]
    try:
        index = []
        # Dashboard views
        views = [
            ("dashboard", "Dashboard", "Main business overview"),
            ("revenue", "Revenue", "Monthly revenue KPI"),
            ("schools", "Schools", "School pipeline from Supabase"),
            ("expenses", "Expenses", "Monthly burn and expenses"),
            ("inbox", "Inbox", "Gmail inbox"),
            ("pillars", "Six Pillars", "OS health pillars"),
            ("memory", "Memory Graph", "Knowledge graph and memory feed"),
            ("wiki", "Wiki Browser", "Browse and search vault wiki pages"),
            ("roi", "ROI", "AI return on investment"),
            ("dreams", "Dreams", "Dream machine recommendations"),
            ("bridge", "GC Bridge", "Hermes bridge"),
            ("wizard", "Setup Wizard", "AIOS configuration wizard"),
            ("supabase", "Supabase", "Database tables and status"),
            ("pinecone", "Pinecone", "Vector memory search"),
            ("usage", "Token Usage", "Token usage and subscription stats"),
            ("agent", "Personal Agent", "AI assistant with vault context"),
            ("finances", "Finances", "Full card burn, top vendors, 4-month trend, interest tracking"),
        ]
        for route, label, ctx in views:
            index.append({"type": "view", "id": route, "label": label, "context": ctx, "route": route, "action_payload": {"view": route}})

        # Domain folders
        from pathlib import Path
        vault = Path(BASE).parent / "Bryan-Aaron-Master"
        for d in sorted(vault.iterdir()):
            import re as _re
            if d.is_dir() and _re.match(r"^\d{2}-", d.name):
                index.append({"type": "domain", "id": f"domain:{d.name}", "label": d.name, "context": "Domain folder", "route": "wiki", "action_payload": {"view": "wiki", "domain": d.name}})

        # Graph nodes from memory-graph
        try:
            from memory_graph import build as build_graph
            gd = build_graph()
            for n in gd.get("nodes", []):
                index.append({
                    "type": "graph",
                    "id": n.get("id"),
                    "label": n.get("label") or n.get("id", ""),
                    "context": n.get("kind", ""),
                    "route": "memory",
                    "action_payload": {"view": "memory", "node_id": n.get("id"), "kind": n.get("kind")},
                })
        except Exception:
            pass

        # Wiki pages
        try:
            t = wiki_mod.tree()
            def _flatten(nodes, prefix=""):
                for node in nodes:
                    if node["type"] == "file":
                        p = node["path"]
                        index.append({"type": "wiki", "id": f"wiki:{p}", "label": node["name"], "context": f"wiki/{p}", "route": "wiki", "action_payload": {"view": "wiki", "wiki_path": p}})
                    elif node["type"] == "dir":
                        _flatten(node.get("children", []), prefix + node["name"] + "/")
            _flatten(t.get("wiki", []))
        except Exception:
            pass

        _search_index_cache["ts"] = now
        _search_index_cache["data"] = index
        return index
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/ag-coach/mirror-refresh")
def api_ag_coach_mirror():
    """Re-run the ag-coach-app .md mirror script into vault App-Source/."""
    import subprocess
    res = subprocess.run(
        [str(SCRIPTS / "mirror_ag_coach.sh")],
        capture_output=True, text=True, timeout=60
    )
    return {"ok": res.returncode == 0, "stdout": res.stdout[-1000:], "stderr": res.stderr[-500:]}


# ── Vault → Pinecone embed ────────────────────────────────────

@app.post("/api/vault/embed")
def api_vault_embed(force: bool = False):
    """Trigger vault → Pinecone embed. Idempotent unless force=true."""
    import subprocess
    cmd = ["python3", str(SCRIPTS / "vault_to_pinecone.py")]
    if force:
        cmd.append("--full")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return {"ok": res.returncode == 0, "stdout": res.stdout[-2000:], "stderr": res.stderr[-1000:]}

@app.get("/api/vault/embed-state")
def api_vault_embed_state():
    state_file = BASE / "data" / "vault_embed_state.json"
    if not state_file.exists():
        return {"files_embedded": 0, "files": {}}
    s = json.loads(state_file.read_text())
    files = s.get("files", {})
    total_chunks = sum(f.get("chunks", 0) for f in files.values())
    return {"files_embedded": len(files), "total_chunks": total_chunks, "last_files": list(files.keys())[-10:]}


# ── AIS-OS L7 extensions: Hermes + revenue + promote + businesses ─────

@app.get("/api/revenue")
def api_revenue():
    """Latest revenue snapshot written by scripts/revenue_snapshot.py."""
    path = DATA / "revenue.json"
    if not path.exists():
        return {"stale": True, "error": "no snapshot yet — run scripts/revenue_snapshot.py"}
    return json.loads(path.read_text())

@app.get("/api/hermes/status")
def api_hermes_status():
    """Latest Hermes status snapshot written by the agent-control skill."""
    path = DATA / "hermes_status.json"
    if not path.exists():
        return {"state": "UNKNOWN", "error": "no snapshot yet — run /agent status"}
    return json.loads(path.read_text())

@app.get("/api/hermes/pantheon")
def api_hermes_pantheon():
    """Read Pantheon persona files from hermes-claw and return agent list."""
    import re
    hermes_root = Path("/Volumes/Samsung PSSD T7/hermes-claw")
    personas_dir = hermes_root / "hermes" / "personas"
    agents = []
    if not personas_dir.exists():
        return {"agents": [], "error": f"personas dir not found: {personas_dir}"}
    for p in sorted(personas_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        text = p.read_text()
        # Parse YAML frontmatter
        meta = {"name": p.stem.title(), "model": "unknown", "role": "agent", "color": "#8E8E93"}
        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip().strip('"').strip("'")
        agents.append({
            "id": p.stem,
            "name": meta.get("name", p.stem.title()),
            "model": meta.get("model", "unknown"),
            "role": meta.get("role", "agent"),
            "color": meta.get("color", "#8E8E93"),
            "state": "standing by",
        })
    return {"agents": agents, "count": len(agents)}

class PromoteRequest(BaseModel):
    card_id: str
    skill_name: str | None = None
    kind: str | None = None
    force: bool = False
    date: str | None = None

@app.post("/api/promote")
def api_promote(body: PromoteRequest):
    """Run the dream→skill promote pipeline for a card id."""
    import subprocess, json as _json
    cmd = ["python3", "-m", "scripts.promote", body.card_id]
    if body.skill_name:
        cmd += ["--skill-name", body.skill_name]
    if body.date:
        cmd += ["--date", body.date]
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    result_json = {}
    try:
        result_json = _json.loads(res.stdout)
    except Exception:
        pass
    return {"ok": res.returncode == 0, "exit_code": res.returncode,
            "stdout": res.stdout, "stderr": res.stderr[-1000:], **result_json}

@app.get("/api/promote/log")
def api_promote_log(limit: int = 20):
    """Tail of the promote log. Supports both JSON-array format (promote.py) and JSONL."""
    path = DATA / "promote.log"
    if not path.exists():
        return {"entries": []}
    raw = path.read_text().strip()
    if not raw:
        return {"entries": []}
    # Try JSON array first (promote.py writes this format)
    try:
        entries = json.loads(raw)
        if isinstance(entries, list):
            return {"entries": entries[-limit:]}
    except json.JSONDecodeError:
        pass
    # Fallback: JSONL (one JSON object per line)
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"entries": entries[-limit:]}

@app.get("/api/businesses")
def api_businesses():
    """List business avenues with status (filled vs stub)."""
    biz_dir = ROOT / "context" / "businesses"
    if not biz_dir.exists():
        return {"items": []}
    items = []
    for path in sorted(biz_dir.glob("*.md")):
        text = path.read_text()
        is_stub = "STUB" in text[:200]
        items.append({
            "slug": path.stem,
            "filled": not is_stub,
            "path": str(path.relative_to(ROOT)),
        })
    return {"items": items}

@app.get("/hermes", response_class=HTMLResponse)
def hermes_panel():
    """Standalone Hermes + dream-promote control panel."""
    html_path = BASE / "hermes-panel.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>hermes-panel.html missing</h1>"


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Ag Coach Pro AIOS Dashboard...")
    print("Opening http://localhost:8080")
    webbrowser.open("http://localhost:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
