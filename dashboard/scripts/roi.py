"""ROI & cost intelligence — monthly spend vs value saved via skills."""
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"

AI_CATEGORIES = {"AI Tools", "AI API", "AI Infrastructure"}


def _load(name: str) -> dict:
    with open(DATA / name) as f:
        return json.load(f)


def compute() -> dict:
    expenses = _load("expenses.json")["expenses"]
    skills_doc = _load("skills.json")
    skills = skills_doc["skills"]
    hourly = skills_doc.get("hourly_rate", 75)

    ai_spend = sum(e["amount"] for e in expenses if e.get("category") in AI_CATEGORIES)
    total_spend = sum(e["amount"] for e in expenses)

    # Value = sum of (value_saved_per_run minutes * runs) converted via hourly rate
    minutes_saved = sum(s["value_saved_per_run"] * s["run_count"] for s in skills)
    value_saved = round(minutes_saved / 60 * hourly, 2)

    net = round(value_saved - ai_spend, 2)

    # Inefficiency flags: skills with opus tier that run frequently on simple-sounding tasks
    flags = []
    for s in skills:
        if s["model_tier"] == "opus" and s["run_count"] >= 3 and s["value_saved_per_run"] < 20:
            flags.append({
                "kind": "expensive-model-cheap-task",
                "skill": s["name"],
                "suggest": "Try Haiku/Sonnet instead — task signature suggests cheap-model is enough",
            })
    for s in skills:
        if s["run_count"] == 0 and s["last_run"] is None:
            flags.append({
                "kind": "skill-never-used",
                "skill": s["name"],
                "suggest": "Never invoked — either delete or wire into a hook",
            })

    return {
        "monthly_ai_spend": round(ai_spend, 2),
        "monthly_total_spend": round(total_spend, 2),
        "monthly_value_saved": value_saved,
        "minutes_saved": minutes_saved,
        "hourly_rate": hourly,
        "net_roi": net,
        "skills": skills,
        "flags": flags,
        "ts": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2))
