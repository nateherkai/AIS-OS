import os
import json
import secrets
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

load_dotenv()

# Paths
BASE = Path(__file__).parent
DATA = BASE / "data"
SCRIPTS = BASE / "scripts"

import sys
sys.path.insert(0, str(SCRIPTS))
from supabase_client import get_schools, get_pipeline_summary
from parse_apple_card import parse_and_update
from pillars import build_pillars
from memory_feed import build_feed as build_memory_feed
from memory_graph import build as build_memory_graph
from roi import compute as compute_roi
import bridge as bridge_mod
import notify_gc
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

# ── Data helpers ──────────────────────────────────────────────

def read_json(name: str) -> dict:
    with open(DATA / name) as f:
        return json.load(f)

def write_json(name: str, data: dict):
    with open(DATA / name, "w") as f:
        json.dump(data, f, indent=2)

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

@app.get("/api/kpis")
def kpis():
    schools = get_schools()
    summary = get_pipeline_summary(schools)
    expenses = read_json("expenses.json")
    debt = read_json("debt.json")
    total_burn = sum(e["amount"] for e in expenses["expenses"])
    # Athens: $1,495/yr = ~$124.58/mo
    monthly_revenue = 124.58 * summary["paid_count"]
    net = monthly_revenue - total_burn
    return {
        "monthly_revenue": round(monthly_revenue, 2),
        "monthly_burn": round(total_burn, 2),
        "net": round(net, 2),
        "paid_schools": summary["paid_count"],
        "trial_schools": summary["trial_count"],
        "school_goal": 50,
        "debt_total_paid": debt["total_paid"],
        "debt_goal": debt["goal"],
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
    total_burn = sum(e["amount"] for e in expenses["expenses"])
    monthly_revenue = 124.58 * summary["paid_count"]
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
        f"MRR: ${monthly_revenue:.2f}  |  Burn: ${total_burn:.2f}  |  Net: ${net:.2f}",
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

@app.post("/api/dreams/run")
def api_dreams_run():
    res = subprocess.run(
        ["python3", str(SCRIPTS / "dream_machine.py")],
        capture_output=True, text=True, timeout=60,
    )
    return {"ok": res.returncode == 0, "stdout": res.stdout[-2000:], "stderr": res.stderr[-1000:]}

# ── Bridge (Gravity Claw two-way) ─────────────────────────────

class BridgeQuery(BaseModel):
    q: str | None = None
    scope: list[str] | None = None

class BridgePush(BaseModel):
    message: str
    event_id: str | None = None

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
    return notify_gc.post(body.message, body.event_id)

@app.post("/api/bridge/local-test")
async def api_bridge_local_test(req: Request):
    """Loopback-only smoke test — sends a Telegram message via GC bot."""
    if req.client.host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(403, "loopback only")
    return notify_gc.post(f"✅ AIOS bridge online — UI test {datetime.now().strftime('%H:%M:%S')}")

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

# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Ag Coach Pro AIOS Dashboard...")
    print("Opening http://localhost:8080")
    webbrowser.open("http://localhost:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
