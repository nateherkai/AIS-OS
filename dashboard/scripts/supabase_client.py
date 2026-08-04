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
    trials = [s for s in schools if s["subscription_status"] in ("trial", "trialing")]
    return {
        "paid_count": len(paid),
        "trial_count": len(trials),
        "paid": paid,
        "trials": trials,
        "school_goal": 50,
        "goal_date": "August 2026",
    }
