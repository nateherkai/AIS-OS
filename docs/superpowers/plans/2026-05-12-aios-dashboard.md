# AIOS Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web dashboard that shows Bryan's Ag Coach Pro revenue, school pipeline, expenses, tasks, and debt tracker in one dark-glass UI — launched with one command.

**Architecture:** FastAPI Python backend serves a single-page HTML frontend. Backend fetches live data from Supabase and Stripe on each request. Expenses stored in local JSON, updated by Apple Card CSV parser. All data served via REST endpoints to the frontend.

**Tech Stack:** Python 3, FastAPI, uvicorn, supabase-py, stripe, python-dotenv, vanilla JS frontend (no framework)

**Spec:** `docs/superpowers/specs/2026-05-12-aios-dashboard-design.md`

---

## File Map

```
AIS-OS/dashboard/
├── server.py                  ← FastAPI app + all API endpoints
├── index.html                 ← Single-page frontend (dark glass)
├── requirements.txt           ← Python dependencies
├── data/
│   ├── expenses.json          ← Expense list (seed + CSV-parsed)
│   ├── tasks.json             ← Today's focus tasks (persisted)
│   └── debt.json              ← Debt payoff log
├── imports/                   ← Drop Apple Card CSVs here
└── scripts/
    ├── supabase_client.py     ← Supabase REST helpers
    └── parse_apple_card.py    ← CSV parser → updates expenses.json
```

---

## Task 1: Project Scaffold + Dependencies

**Files:**
- Create: `dashboard/requirements.txt`
- Create: `dashboard/data/expenses.json`
- Create: `dashboard/data/tasks.json`
- Create: `dashboard/data/debt.json`
- Create: `dashboard/imports/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn==0.30.0
supabase==2.7.0
stripe==10.0.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Install dependencies**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
pip3 install -r dashboard/requirements.txt --break-system-packages
```

Expected: all packages install without error.

- [ ] **Step 3: Create seed expenses.json**

```json
{
  "expenses": [
    {"name": "Claude Max", "category": "AI Tools", "amount": 130, "vendor_match": ["ANTHROPIC", "CLAUDE"]},
    {"name": "Supabase", "category": "Infrastructure", "amount": 25, "vendor_match": ["SUPABASE"]},
    {"name": "Vercel", "category": "Infrastructure", "amount": 20, "vendor_match": ["VERCEL"]},
    {"name": "Google Workspace", "category": "Productivity", "amount": 20, "vendor_match": ["GOOGLE"]},
    {"name": "ChatGPT Plus", "category": "AI Tools", "amount": 20, "vendor_match": ["OPENAI"]},
    {"name": "Firecrawl", "category": "AI API", "amount": 19, "vendor_match": ["FIRECRAWL"]},
    {"name": "MailerLite", "category": "Marketing", "amount": 15, "vendor_match": ["MAILERLITE"]},
    {"name": "Pinecone", "category": "AI Infrastructure", "amount": 0, "vendor_match": ["PINECONE"]},
    {"name": "Fal.ai", "category": "AI API", "amount": 0, "vendor_match": ["FAL"]}
  ],
  "last_updated": null
}
```

Save to `dashboard/data/expenses.json`.

- [ ] **Step 4: Create seed tasks.json**

```json
{
  "tasks": [
    {"id": 1, "text": "Follow up with 5 trial schools", "tag": "Sales", "done": false},
    {"id": 2, "text": "Reply to Trinity — livestock feedback", "tag": "Support", "done": false},
    {"id": 3, "text": "Send MailerLite blast to 560 teachers", "tag": "Marketing", "done": false}
  ]
}
```

Save to `dashboard/data/tasks.json`.

- [ ] **Step 5: Create seed debt.json**

```json
{
  "payments": [],
  "total_paid": 0,
  "goal": 50000,
  "goal_date": "2026-12-31"
}
```

Save to `dashboard/data/debt.json`.

- [ ] **Step 6: Create imports directory**

```bash
mkdir -p "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/imports"
touch "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/imports/.gitkeep"
```

- [ ] **Step 7: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
git add dashboard/
git commit -m "feat(dashboard): scaffold project structure and seed data"
```

---

## Task 2: Supabase Client Module

**Files:**
- Create: `dashboard/scripts/supabase_client.py`

- [ ] **Step 1: Create supabase_client.py**

```python
import os
from dotenv import load_dotenv
import urllib.request
import json

load_dotenv()

SUPABASE_URL = os.environ["EXPO_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def _get(path: str) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_schools() -> list:
    """Return all non-seed schools with status and tier."""
    rows = _get("schools?select=id,name,advisor_name,advisor_email,subscription_status,subscription_tier,max_students,created_at&order=created_at.asc")
    return [r for r in rows if not r["id"].startswith("11111111")]

def get_pipeline_summary(schools: list) -> dict:
    paid = [s for s in schools if s["subscription_status"] == "active"]
    trials = [s for s in schools if s["subscription_status"] == "trialing"]
    return {
        "paid_count": len(paid),
        "trial_count": len(trials),
        "paid": paid,
        "trials": trials,
        "goal": 50,
        "goal_date": "August 2026",
    }
```

- [ ] **Step 2: Smoke test**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 -c "
import sys; sys.path.insert(0, 'dashboard/scripts')
from supabase_client import get_schools, get_pipeline_summary
schools = get_schools()
summary = get_pipeline_summary(schools)
print('Schools:', len(schools))
print('Paid:', summary['paid_count'])
print('Trials:', summary['trial_count'])
"
```

Expected output:
```
Schools: 6
Paid: 1
Trials: 5
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/scripts/supabase_client.py
git commit -m "feat(dashboard): add Supabase client for school pipeline data"
```

---

## Task 3: Apple Card CSV Parser

**Files:**
- Create: `dashboard/scripts/parse_apple_card.py`

- [ ] **Step 1: Create parse_apple_card.py**

```python
"""
Parse Apple Card CSV exports and update expenses.json with actual amounts.
Apple Card CSV format:
  Transaction Date,Clearing Date,Description,Merchant,Category,Type,Amount (USD)
"""
import csv
import json
import os
import glob
from datetime import datetime

IMPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "imports")
EXPENSES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "expenses.json")

def find_latest_csv() -> str | None:
    pattern = os.path.join(IMPORTS_DIR, "*.csv")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None

def match_vendor(description: str, merchant: str, vendor_keywords: list[str]) -> bool:
    text = (description + " " + merchant).upper()
    return any(kw.upper() in text for kw in vendor_keywords)

def parse_and_update():
    csv_path = find_latest_csv()
    if not csv_path:
        return {"updated": False, "reason": "No CSV found in imports/"}

    with open(EXPENSES_FILE) as f:
        data = json.load(f)

    # Accumulate charges per expense by vendor match
    charges: dict[str, float] = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row.get("Description", "") or row.get("Merchant", "")
            merchant = row.get("Merchant", "")
            try:
                amount = abs(float(row.get("Amount (USD)", 0) or 0))
            except ValueError:
                continue
            for expense in data["expenses"]:
                if match_vendor(desc, merchant, expense["vendor_match"]):
                    charges[expense["name"]] = charges.get(expense["name"], 0) + amount

    # Update amounts where CSV data found
    updated = []
    for expense in data["expenses"]:
        if expense["name"] in charges:
            expense["amount"] = round(charges[expense["name"]], 2)
            updated.append(expense["name"])

    data["last_updated"] = datetime.now().isoformat()

    with open(EXPENSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {"updated": True, "updated_vendors": updated, "csv_file": os.path.basename(csv_path)}

if __name__ == "__main__":
    result = parse_and_update()
    print(result)
```

- [ ] **Step 2: Test with no CSV (should return gracefully)**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 dashboard/scripts/parse_apple_card.py
```

Expected:
```
{'updated': False, 'reason': 'No CSV found in imports/'}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/scripts/parse_apple_card.py
git commit -m "feat(dashboard): add Apple Card CSV parser for expense auto-update"
```

---

## Task 4: FastAPI Server

**Files:**
- Create: `dashboard/server.py`

- [ ] **Step 1: Create server.py**

```python
import os
import json
import webbrowser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
        f"TRIALS GOING COLD (>14 days)",
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

# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Ag Coach Pro AIOS Dashboard...")
    print("Opening http://localhost:8080")
    webbrowser.open("http://localhost:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
```

- [ ] **Step 2: Smoke test server starts**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
timeout 5 python3 dashboard/server.py || true
```

Expected: server starts, prints startup message, exits after 5s (timeout).

- [ ] **Step 3: Test API endpoints**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 dashboard/server.py &
sleep 2
curl -s http://localhost:8080/api/expenses | python3 -m json.tool | head -20
curl -s http://localhost:8080/api/tasks | python3 -m json.tool
kill %1
```

Expected: JSON responses with expense list and tasks.

- [ ] **Step 4: Commit**

```bash
git add dashboard/server.py
git commit -m "feat(dashboard): add FastAPI server with pipeline, expenses, tasks, debt endpoints"
```

---

## Task 5: Frontend HTML — Structure + Dark Glass CSS

**Files:**
- Create: `dashboard/index.html`

- [ ] **Step 1: Create index.html with full dark glass UI**

Create `dashboard/index.html` with the following content (this is the complete file — paste it fully):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ag Coach Pro — AIOS Dashboard</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#050510; color:#e0e0e0; font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display',sans-serif; height:100vh; display:flex; overflow:hidden; }
.glass { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); backdrop-filter:blur(20px); }
.glass-gold { background:rgba(212,165,116,0.08); border:1px solid rgba(212,165,116,0.25); backdrop-filter:blur(20px); }

/* SIDEBAR */
.sidebar { width:220px; min-width:220px; height:100vh; background:rgba(0,0,0,0.5); border-right:1px solid rgba(255,255,255,0.06); display:flex; flex-direction:column; padding:24px 16px; gap:2px; }
.sidebar-logo { display:flex; align-items:center; gap:10px; padding:0 8px 20px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:10px; }
.logo-mark { width:32px; height:32px; background:linear-gradient(135deg,#D4A574,#c4855a); border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:14px; color:#001F4D; }
.logo-text { font-size:13px; font-weight:600; color:#fff; }
.logo-sub { font-size:10px; color:rgba(255,255,255,0.35); }
.nav-item { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:8px; font-size:13px; color:rgba(255,255,255,0.45); cursor:pointer; transition:all 0.15s; border:1px solid transparent; user-select:none; }
.nav-item:hover { background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.8); }
.nav-item.active { background:rgba(212,165,116,0.12); color:#D4A574; border-color:rgba(212,165,116,0.2); }
.nav-icon { font-size:14px; width:18px; text-align:center; }
.nav-label { flex:1; }
.nav-badge { background:#D4A574; color:#001F4D; font-size:10px; font-weight:700; padding:2px 6px; border-radius:10px; }
.sidebar-section { font-size:10px; font-weight:600; letter-spacing:0.08em; color:rgba(255,255,255,0.2); text-transform:uppercase; padding:14px 12px 5px; }
.sidebar-spacer { flex:1; }
.sidebar-bottom { font-size:11px; color:rgba(255,255,255,0.3); padding:12px 12px 0; border-top:1px solid rgba(255,255,255,0.06); line-height:1.9; }
.action-btn { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:8px; font-size:12px; color:rgba(255,255,255,0.5); cursor:pointer; transition:all 0.15s; border:1px solid rgba(255,255,255,0.06); margin-top:2px; background:rgba(255,255,255,0.02); }
.action-btn:hover { background:rgba(212,165,116,0.1); color:#D4A574; border-color:rgba(212,165,116,0.25); transform:translateX(2px); }

/* MAIN */
.main { flex:1; overflow-y:auto; padding:24px 28px; display:flex; flex-direction:column; gap:16px; }
.page-header { display:flex; align-items:center; justify-content:space-between; }
.page-title { font-size:22px; font-weight:700; color:#fff; }
.page-date { font-size:12px; color:rgba(255,255,255,0.3); }
.refresh-btn { font-size:11px; color:rgba(212,165,116,0.6); border:1px solid rgba(212,165,116,0.2); border-radius:6px; padding:4px 10px; cursor:pointer; background:rgba(212,165,116,0.05); }
.refresh-btn:hover { background:rgba(212,165,116,0.12); color:#D4A574; }

/* NET BANNER */
.net-banner { border-radius:12px; padding:12px 20px; display:flex; align-items:center; justify-content:space-between; }
.net-banner.negative { background:rgba(248,113,113,0.07); border:1px solid rgba(248,113,113,0.2); }
.net-banner.positive { background:rgba(74,222,128,0.07); border:1px solid rgba(74,222,128,0.2); }
.net-label { font-size:11px; color:rgba(255,255,255,0.4); margin-bottom:2px; }
.net-value { font-size:22px; font-weight:700; }
.net-value.red { color:#f87171; }
.net-value.green { color:#4ade80; }
.net-note { font-size:11px; color:rgba(255,255,255,0.3); }

/* KPI */
.kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.kpi-card { border-radius:14px; padding:16px 18px; }
.kpi-label { font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(255,255,255,0.35); margin-bottom:6px; }
.kpi-value { font-size:26px; font-weight:700; color:#fff; line-height:1; }
.kpi-value.gold { color:#D4A574; }
.kpi-value.red { color:#f87171; }
.kpi-value.yellow { color:#facc15; }
.kpi-sub { font-size:10px; color:rgba(255,255,255,0.3); margin-top:5px; }
.kpi-progress { height:3px; background:rgba(255,255,255,0.07); border-radius:2px; margin-top:9px; }
.kpi-progress-fill { height:100%; border-radius:2px; background:linear-gradient(90deg,#D4A574,#c4855a); transition:width 0.6s ease; }

/* GRID */
.grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; }
.panel { border-radius:14px; padding:18px; }
.panel-title { font-size:10px; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; color:rgba(255,255,255,0.35); margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; }
.panel-title span { color:#D4A574; font-size:9px; }

/* PIPELINE */
.pipeline-item { display:flex; align-items:center; gap:9px; padding:8px 4px; border-bottom:1px solid rgba(255,255,255,0.04); font-size:12px; cursor:pointer; border-radius:4px; transition:background 0.1s; }
.pipeline-item:hover { background:rgba(255,255,255,0.03); }
.pipeline-item:last-child { border:none; }
.pipeline-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.dot-paid { background:#4ade80; box-shadow:0 0 6px rgba(74,222,128,0.4); }
.dot-trial { background:#facc15; }
.pipeline-name { flex:1; color:rgba(255,255,255,0.75); }
.pipeline-tier { font-size:9px; padding:2px 7px; border-radius:5px; background:rgba(212,165,116,0.12); color:#D4A574; }
.pipeline-tier.trial { background:rgba(250,204,21,0.1); color:#facc15; }

/* EXPENSES */
.expense-item { display:flex; align-items:center; gap:10px; padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.expense-item:last-child { border:none; }
.expense-bar-wrap { flex:1; }
.expense-name { color:rgba(255,255,255,0.65); margin-bottom:3px; font-size:11px; }
.expense-bar { height:3px; background:rgba(255,255,255,0.05); border-radius:2px; }
.expense-bar-fill { height:100%; border-radius:2px; background:rgba(248,113,113,0.5); }
.expense-amt { font-size:12px; color:#f87171; font-weight:500; min-width:40px; text-align:right; }

/* TASKS */
.task-item { display:flex; align-items:flex-start; gap:10px; padding:8px 4px; border-bottom:1px solid rgba(255,255,255,0.04); cursor:pointer; border-radius:4px; transition:all 0.2s; }
.task-item:hover { background:rgba(255,255,255,0.02); }
.task-item:last-child { border:none; }
.task-item.done .task-text { text-decoration:line-through; color:rgba(255,255,255,0.25); }
.task-check { width:16px; height:16px; border-radius:50%; border:1.5px solid rgba(212,165,116,0.35); flex-shrink:0; margin-top:2px; transition:all 0.2s; display:flex; align-items:center; justify-content:center; font-size:9px; }
.task-item.done .task-check { background:rgba(74,222,128,0.2); border-color:#4ade80; color:#4ade80; }
.task-text { color:rgba(255,255,255,0.72); flex:1; font-size:12px; }
.task-tag { font-size:9px; padding:2px 6px; border-radius:5px; background:rgba(212,165,116,0.08); color:rgba(212,165,116,0.7); }

/* DEBT */
.debt-amount { font-size:28px; font-weight:700; color:#4ade80; text-align:center; padding:8px 0 4px; }
.debt-label { font-size:10px; color:rgba(255,255,255,0.3); text-align:center; }
.debt-progress { height:6px; background:rgba(255,255,255,0.05); border-radius:3px; margin-top:10px; }
.debt-progress-fill { height:100%; border-radius:3px; background:linear-gradient(90deg,#4ade80,#22c55e); transition:width 0.6s ease; }
.debt-stats { display:flex; justify-content:space-between; margin-top:6px; font-size:10px; color:rgba(255,255,255,0.25); }
.debt-input-row { display:flex; gap:6px; margin-top:12px; }
.debt-input { flex:1; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:6px; color:#fff; font-size:11px; padding:6px 10px; outline:none; }
.debt-input:focus { border-color:rgba(212,165,116,0.3); }
.debt-log-btn { background:rgba(212,165,116,0.15); border:1px solid rgba(212,165,116,0.3); color:#D4A574; border-radius:6px; font-size:11px; padding:6px 10px; cursor:pointer; }
.debt-log-btn:hover { background:rgba(212,165,116,0.25); }

/* MODAL */
.modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); z-index:100; align-items:center; justify-content:center; }
.modal-overlay.open { display:flex; }
.modal { background:#0d0d1f; border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:28px; max-width:520px; width:90%; max-height:80vh; overflow-y:auto; }
.modal-title { font-size:16px; font-weight:600; color:#fff; margin-bottom:4px; }
.modal-sub { font-size:12px; color:rgba(255,255,255,0.4); margin-bottom:18px; }
.modal-close { float:right; background:none; border:none; color:rgba(255,255,255,0.4); cursor:pointer; font-size:20px; margin-top:-4px; }
.modal-result { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:14px; font-size:12px; line-height:1.8; color:rgba(255,255,255,0.7); white-space:pre-wrap; font-family:monospace; }
.modal-action { margin-top:16px; display:flex; gap:8px; }
.btn-primary { flex:1; background:rgba(212,165,116,0.2); border:1px solid rgba(212,165,116,0.4); color:#D4A574; border-radius:8px; font-size:12px; padding:9px; cursor:pointer; font-weight:500; }
.btn-primary:hover { background:rgba(212,165,116,0.3); }
.btn-secondary { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); color:rgba(255,255,255,0.5); border-radius:8px; font-size:12px; padding:9px 14px; cursor:pointer; }

/* TOAST */
.toast { position:fixed; bottom:24px; right:24px; background:rgba(212,165,116,0.15); border:1px solid rgba(212,165,116,0.35); color:#D4A574; border-radius:10px; padding:10px 16px; font-size:12px; z-index:200; opacity:0; transform:translateY(10px); transition:all 0.25s; pointer-events:none; }
.toast.show { opacity:1; transform:translateY(0); }

/* LOADING */
.loading { color:rgba(255,255,255,0.2); font-size:11px; text-align:center; padding:20px; }
</style>
</head>
<body>

<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-title" id="modal-title"></div>
    <div class="modal-sub" id="modal-sub"></div>
    <div class="modal-result" id="modal-body"></div>
    <div class="modal-action">
      <button class="btn-primary" onclick="closeModal()">Done</button>
      <button class="btn-secondary" onclick="closeModal()">Close</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<!-- SIDEBAR -->
<div class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-mark">AC</div>
    <div><div class="logo-text">Ag Coach Pro</div><div class="logo-sub">Business OS</div></div>
  </div>
  <div class="nav-item active"><span class="nav-icon">⌂</span><span class="nav-label">Dashboard</span></div>
  <div class="nav-item"><span class="nav-icon">$</span><span class="nav-label">Revenue</span></div>
  <div class="nav-item"><span class="nav-icon">🏫</span><span class="nav-label">Schools</span><span class="nav-badge" id="sb-trials">—</span></div>
  <div class="nav-item"><span class="nav-icon">↓</span><span class="nav-label">Expenses</span></div>
  <div class="nav-item"><span class="nav-icon">✉</span><span class="nav-label">Inbox</span></div>
  <div class="sidebar-section">Skills</div>
  <div class="action-btn" onclick="runPipelineCheck()"><span class="nav-icon">▶</span><span>Pipeline Check</span></div>
  <div class="action-btn" onclick="openModal('✍ Draft Reply','Run /draft-reply in Claude Code and paste the incoming email.','Skill: /draft-reply\n\nHow to use:\n1. Open Claude Code in the AIS-OS directory\n2. Type: /draft-reply\n3. Paste the incoming email when prompted\n4. Review draft — copy and send manually')"><span class="nav-icon">✍</span><span>Draft Reply</span></div>
  <div class="action-btn" onclick="runTrialFollowUp()"><span class="nav-icon">↑</span><span>Trial Follow-Up</span></div>
  <div class="action-btn" onclick="syncExpenses()"><span class="nav-icon">⟳</span><span>Sync Receipts</span></div>
  <div class="sidebar-spacer"></div>
  <div class="sidebar-bottom">
    Burn: <span id="sb-burn" style="color:#f87171;font-weight:600;">—</span><br>
    Revenue: <span id="sb-rev" style="color:#4ade80;font-weight:600;">—</span><br>
    Net: <span id="sb-net" style="font-weight:600;">—</span>
  </div>
</div>

<!-- MAIN -->
<div class="main">
  <div class="page-header">
    <div class="page-title" id="greeting">Good morning, Bryan</div>
    <div style="display:flex;align-items:center;gap:12px;">
      <button class="refresh-btn" onclick="loadAll()">↺ Refresh</button>
      <div class="page-date" id="live-date"></div>
    </div>
  </div>

  <!-- Net banner -->
  <div class="net-banner negative" id="net-banner">
    <div>
      <div class="net-label">Current Net Income</div>
      <div class="net-note" id="net-note">Loading...</div>
    </div>
    <div class="net-value red" id="net-value">—</div>
  </div>

  <!-- KPIs -->
  <div class="kpi-row">
    <div class="kpi-card glass-gold">
      <div class="kpi-label">Monthly Revenue</div>
      <div class="kpi-value gold" id="kpi-revenue">—</div>
      <div class="kpi-sub" id="kpi-revenue-sub">loading...</div>
      <div class="kpi-progress"><div class="kpi-progress-fill" id="prog-revenue" style="width:0%"></div></div>
    </div>
    <div class="kpi-card glass">
      <div class="kpi-label">School Goal</div>
      <div class="kpi-value" id="kpi-schools">—</div>
      <div class="kpi-sub">goal: 50 · deadline Aug 2026</div>
      <div class="kpi-progress"><div class="kpi-progress-fill" id="prog-schools" style="width:0%"></div></div>
    </div>
    <div class="kpi-card glass">
      <div class="kpi-label">Monthly Burn</div>
      <div class="kpi-value red" id="kpi-burn">—</div>
      <div class="kpi-sub" id="kpi-burn-sub">loading...</div>
    </div>
    <div class="kpi-card glass">
      <div class="kpi-label">Active Trials</div>
      <div class="kpi-value yellow" id="kpi-trials">—</div>
      <div class="kpi-sub" id="kpi-trials-sub">loading...</div>
    </div>
  </div>

  <!-- Schools + Expenses -->
  <div class="grid-2">
    <div class="panel glass">
      <div class="panel-title">School Pipeline <span>LIVE · SUPABASE</span></div>
      <div id="pipeline-list"><div class="loading">Loading...</div></div>
    </div>
    <div class="panel glass">
      <div class="panel-title">Monthly Expenses <span id="expense-total-label">loading...</span></div>
      <div id="expense-list"><div class="loading">Loading...</div></div>
    </div>
  </div>

  <!-- Tasks + Debt -->
  <div class="grid-2">
    <div class="panel glass">
      <div class="panel-title">Today's Focus <span id="tasks-done-label">0/3 DONE</span></div>
      <div id="task-list"><div class="loading">Loading...</div></div>
    </div>
    <div class="panel glass">
      <div class="panel-title">Debt Payoff <span>GOAL: DEC 2026</span></div>
      <div class="debt-amount" id="debt-paid">$0</div>
      <div class="debt-label">paid off this year</div>
      <div class="debt-progress"><div class="debt-progress-fill" id="debt-bar" style="width:0%"></div></div>
      <div class="debt-stats"><span id="debt-pct">0% complete</span><span>Dec 31, 2026</span></div>
      <div class="debt-input-row">
        <input class="debt-input" id="debt-input" placeholder="Log payment amount ($)" type="number" min="1">
        <button class="debt-log-btn" onclick="logDebt()">Log</button>
      </div>
    </div>
  </div>
</div>

<script>
// ── Init ──────────────────────────────────────────────────────

const now = new Date();
const hour = now.getHours();
const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
document.getElementById('greeting').textContent = `${greeting}, Bryan`;
document.getElementById('live-date').textContent = now.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'});

// ── Helpers ───────────────────────────────────────────────────

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function openModal(title, sub, body) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-sub').textContent = sub;
  document.getElementById('modal-body').textContent = body;
  document.getElementById('modal').classList.add('open');
}
function closeModal() { document.getElementById('modal').classList.remove('open'); }

async function api(path, opts={}) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ── KPIs ──────────────────────────────────────────────────────

async function loadKPIs() {
  const d = await api('/api/kpis');
  const rev = d.monthly_revenue;
  const burn = d.monthly_burn;
  const net = d.net;
  const paidPct = Math.min((d.paid_schools / d.school_goal) * 100, 100);
  const revGoalPct = Math.min((rev / 10000) * 100, 100);

  document.getElementById('kpi-revenue').textContent = `$${rev.toFixed(0)}`;
  document.getElementById('kpi-revenue-sub').textContent = `${d.paid_schools} school${d.paid_schools !== 1 ? 's' : ''} paid`;
  document.getElementById('prog-revenue').style.width = revGoalPct + '%';

  document.getElementById('kpi-schools').innerHTML = `${d.paid_schools}<span style="font-size:14px;color:rgba(255,255,255,0.25)">/${d.school_goal}</span>`;
  document.getElementById('prog-schools').style.width = paidPct + '%';

  document.getElementById('kpi-burn').textContent = `$${burn.toFixed(0)}`;
  document.getElementById('kpi-burn-sub').textContent = 'monthly total';

  document.getElementById('kpi-trials').textContent = d.trial_count;
  document.getElementById('kpi-trials-sub').textContent = d.trial_count === 0 ? 'no active trials' : `${d.trial_count} school${d.trial_count !== 1 ? 's' : ''} in trial`;

  // Net banner
  const netEl = document.getElementById('net-value');
  const banner = document.getElementById('net-banner');
  const needed = Math.ceil(Math.abs(net) / 124.58);
  netEl.textContent = (net >= 0 ? '+' : '') + `$${net.toFixed(0)}/mo`;
  netEl.className = 'net-value ' + (net >= 0 ? 'green' : 'red');
  banner.className = 'net-banner ' + (net >= 0 ? 'positive' : 'negative');
  document.getElementById('net-note').textContent = net < 0
    ? `Close ${needed} more school${needed !== 1 ? 's' : ''} to break even. ${d.school_goal - d.paid_schools} to hit goal.`
    : `Profitable. ${d.school_goal - d.paid_schools} schools to hit goal.`;

  // Sidebar summary
  document.getElementById('sb-burn').textContent = `$${burn.toFixed(0)}/mo`;
  document.getElementById('sb-rev').textContent = `$${rev.toFixed(0)}/mo`;
  const sbNet = document.getElementById('sb-net');
  sbNet.textContent = (net >= 0 ? '+' : '') + `$${net.toFixed(0)}/mo`;
  sbNet.style.color = net >= 0 ? '#4ade80' : '#f87171';
}

// ── Pipeline ──────────────────────────────────────────────────

async function loadPipeline() {
  const d = await api('/api/pipeline');
  document.getElementById('sb-trials').textContent = d.trial_count || '0';

  const all = [...d.paid, ...d.trials];
  const list = document.getElementById('pipeline-list');
  if (all.length === 0) {
    list.innerHTML = '<div class="loading">No schools yet</div>';
    return;
  }
  list.innerHTML = all.map(s => {
    const isPaid = s.subscription_status === 'active';
    const tier = isPaid ? (s.subscription_tier === 'enterprise' ? 'Lone Star Elite' : 'Blue & Gold') : `Trial · ${s.days_in_trial || 0}d`;
    const tierClass = isPaid ? '' : 'trial';
    return `<div class="pipeline-item" onclick="showSchool('${s.name}','${s.advisor_name||''}','${tier}','${s.advisor_email||'No email on file'}')">
      <div class="pipeline-dot ${isPaid ? 'dot-paid' : 'dot-trial'}"></div>
      <div class="pipeline-name">${s.name}${s.advisor_name ? ' — ' + s.advisor_name : ''}</div>
      <div class="pipeline-tier ${tierClass}">${tier}</div>
    </div>`;
  }).join('');
}

function showSchool(name, advisor, tier, email) {
  openModal(name, `${advisor} · ${tier}`, `Email: ${email}\nTier: ${tier}\n\nRun /trial-follow-up in Claude Code to draft a personalized close email.`);
}

// ── Expenses ──────────────────────────────────────────────────

async function loadExpenses() {
  const d = await api('/api/expenses');
  const max = Math.max(...d.expenses.map(e => e.amount), 1);
  document.getElementById('expense-total-label').textContent = `$${d.total.toFixed(0)} TOTAL BURN`;
  const sorted = [...d.expenses].sort((a,b) => b.amount - a.amount).filter(e => e.amount > 0);
  document.getElementById('expense-list').innerHTML = sorted.map(e =>
    `<div class="expense-item">
      <div class="expense-bar-wrap">
        <div class="expense-name">${e.name}</div>
        <div class="expense-bar"><div class="expense-bar-fill" style="width:${(e.amount/max*100).toFixed(0)}%"></div></div>
      </div>
      <div class="expense-amt">$${e.amount}</div>
    </div>`
  ).join('');
}

async function syncExpenses() {
  showToast('Syncing receipts...');
  const r = await api('/api/expenses/sync', {method:'POST'});
  if (r.updated) {
    showToast(`Updated: ${r.updated_vendors.join(', ')}`);
    loadExpenses();
  } else {
    showToast(r.reason || 'No CSV found in dashboard/imports/');
  }
}

// ── Tasks ─────────────────────────────────────────────────────

let tasks = [];

async function loadTasks() {
  const d = await api('/api/tasks');
  tasks = d.tasks;
  renderTasks();
}

function renderTasks() {
  const done = tasks.filter(t => t.done).length;
  document.getElementById('tasks-done-label').textContent = `${done}/${tasks.length} DONE`;
  document.getElementById('task-list').innerHTML = tasks.map(t =>
    `<div class="task-item ${t.done ? 'done' : ''}" onclick="toggleTask(${t.id})">
      <div class="task-check">${t.done ? '✓' : ''}</div>
      <div class="task-text">${t.text}</div>
      <div class="task-tag">${t.tag}</div>
    </div>`
  ).join('');
}

async function toggleTask(id) {
  const t = tasks.find(t => t.id === id);
  if (!t) return;
  t.done = !t.done;
  renderTasks();
  await api('/api/tasks/update', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id, done: t.done})});
  showToast(t.done ? 'Task complete' : 'Task unchecked');
  if (tasks.every(t => t.done)) showToast('All tasks done today!');
}

// ── Debt ──────────────────────────────────────────────────────

async function loadDebt() {
  const d = await api('/api/debt');
  updateDebtUI(d.total_paid, d.goal);
}

function updateDebtUI(paid, goal) {
  const pct = Math.min((paid / goal) * 100, 100).toFixed(1);
  document.getElementById('debt-paid').textContent = '$' + paid.toLocaleString();
  document.getElementById('debt-bar').style.width = pct + '%';
  document.getElementById('debt-pct').textContent = pct + '% complete';
}

async function logDebt() {
  const val = parseFloat(document.getElementById('debt-input').value);
  if (!val || val <= 0) { showToast('Enter a valid amount'); return; }
  const d = await api('/api/debt/log', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({amount: val, note: ''})});
  updateDebtUI(d.total_paid, 50000);
  document.getElementById('debt-input').value = '';
  showToast(`Logged: $${val.toLocaleString()}`);
}

// ── Skills ────────────────────────────────────────────────────

async function runPipelineCheck() {
  showToast('Running pipeline check...');
  const d = await api('/api/skills/pipeline-check');
  openModal('▶ Weekly Pipeline Check', 'Live data from Supabase', d.output);
}

async function runTrialFollowUp() {
  const d = await api('/api/pipeline');
  const trials = d.trials;
  if (trials.length === 0) {
    openModal('↑ Trial Follow-Up', 'No active trials', 'No schools in trial right now.\n\nRun a new MailerLite blast to build pipeline.');
    return;
  }
  const lines = trials.map(s =>
    `• ${s.name}\n  ${s.advisor_name || 'No advisor'} — ${s.advisor_email || 'no email'}\n  ${s.days_in_trial || 0} days in trial`
  ).join('\n\n');
  openModal('↑ Trial Follow-Up', `${trials.length} active trial${trials.length !== 1 ? 's' : ''}`, `Run /trial-follow-up in Claude Code for personalized close emails.\n\n${lines}`);
}

// ── Load all ──────────────────────────────────────────────────

async function loadAll() {
  await Promise.all([loadKPIs(), loadPipeline(), loadExpenses(), loadTasks(), loadDebt()]);
}

loadAll();

// Auto-refresh every 5 minutes
setInterval(loadAll, 5 * 60 * 1000);
</script>
</body>
</html>
```

- [ ] **Step 2: Test frontend loads**

Start server, open browser:
```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 dashboard/server.py &
sleep 2
curl -s http://localhost:8080/ | head -5
kill %1
```

Expected: HTML response starting with `<!DOCTYPE html>`.

- [ ] **Step 3: Commit**

```bash
git add dashboard/index.html
git commit -m "feat(dashboard): add dark glass frontend with all 7 panels"
```

---

## Task 6: Launch Script + README Entry

**Files:**
- Create: `dashboard/launch.sh`
- Modify: `README.md` (or create if missing)

- [ ] **Step 1: Create launch.sh**

```bash
#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting Ag Coach Pro AIOS Dashboard..."
python3 dashboard/server.py
```

- [ ] **Step 2: Make executable**

```bash
chmod +x "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/launch.sh"
```

- [ ] **Step 3: Test launch script**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
timeout 4 bash dashboard/launch.sh || true
```

Expected: prints "Starting Ag Coach Pro AIOS Dashboard...", exits after 4s.

- [ ] **Step 4: Add to README.md**

If `README.md` exists, add this section. If not, create it.

```markdown
## AIOS Dashboard

Local business dashboard — revenue, school pipeline, expenses, tasks, debt tracker.

**Launch:**
```bash
bash dashboard/launch.sh
```

Opens at http://localhost:8080.

**Expense sync (monthly):**
1. Export CSV from Apple Card (Wallet app → Card → Export Transactions)
2. Drop CSV into `dashboard/imports/`
3. Click "Sync Receipts" in the dashboard sidebar
```

- [ ] **Step 5: Commit**

```bash
git add dashboard/launch.sh README.md
git commit -m "feat(dashboard): add launch script and README instructions"
```

---

## Task 7: End-to-End Smoke Test

- [ ] **Step 1: Start dashboard**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 dashboard/server.py &
sleep 2
```

- [ ] **Step 2: Test all API endpoints**

```bash
echo "=== /api/kpis ===" && curl -s http://localhost:8080/api/kpis | python3 -m json.tool | grep -E "net|paid_schools|trial"
echo "=== /api/pipeline ===" && curl -s http://localhost:8080/api/pipeline | python3 -m json.tool | grep -E "paid_count|trial_count"
echo "=== /api/expenses ===" && curl -s http://localhost:8080/api/expenses | python3 -m json.tool | grep total
echo "=== /api/tasks ===" && curl -s http://localhost:8080/api/tasks | python3 -m json.tool | grep text
echo "=== /api/debt ===" && curl -s http://localhost:8080/api/debt | python3 -m json.tool
echo "=== /api/skills/pipeline-check ===" && curl -s http://localhost:8080/api/skills/pipeline-check | python3 -m json.tool | grep output
```

Expected: all endpoints return valid JSON with real data.

- [ ] **Step 3: Open in browser and verify**

```bash
open http://localhost:8080
```

Verify manually:
- Net banner shows -$104/mo (red)
- KPIs show: 1 paid school, $229 burn, 5 trials
- Pipeline shows Athens + 5 trial schools
- Expenses show all 7 services
- Tasks load and can be checked off
- Debt tracker accepts input
- Pipeline Check button shows output modal
- Trial Follow-Up shows all 5 schools

- [ ] **Step 4: Stop server**

```bash
kill %1
```

- [ ] **Step 5: Final commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
git add -A
git commit -m "feat(dashboard): complete Phase 1 — local AIOS dashboard with live Supabase data"
```

---

## Self-Review

**Spec coverage check:**
- ✓ Local web app (Python FastAPI server, `localhost:8080`)
- ✓ 7 panels: net banner, 4 KPIs, pipeline, expenses, tasks, debt, skills
- ✓ Supabase live data (schools/trials)
- ✓ Stripe skipped Phase 1 — spec says Phase 2 (revenue calc uses fixed $124.58/school)
- ✓ Apple Card CSV parser (`parse_apple_card.py`)
- ✓ Manual expense seed data
- ✓ Tasks persisted to JSON
- ✓ Debt tracker persisted to JSON
- ✓ Skill modals (pipeline-check, draft-reply, trial-follow-up)
- ✓ Dark glass aesthetic matching Ag Coach Pro brand
- ✓ Launch command: `python3 dashboard/server.py`
- ✓ Auto-refresh every 5 minutes

**Phase 2 items (not in this plan — build after Phase 1 validated):**
- Gmail inbox triage panel
- Gmail receipt parser
- Stripe live subscription data
- Inline task editing

**No placeholders found.** All code is complete.
