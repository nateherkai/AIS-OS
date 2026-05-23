"""promote.py — Dream card → real Hermes SKILL.md

Called by /api/promote as:  python3 -m scripts.promote <card_id> [--skill-name <name>] [--date <YYYY-MM-DD>]

What it does:
  1. Reads the dream card from the latest (or specified) dream JSON.
  2. Generates a proper Hermes SKILL.md from the card metadata.
  3. Writes the skill to hermes-claw/skills/<slug>/SKILL.md.
  4. Marks the card status = "promoted" in the dream JSON.
  5. Prints a JSON result with the skill path.

Exit codes: 0 = success, 1 = error.
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
DREAMS_DIR = DATA / "dreams"
HERMES_SKILLS = Path("/Volumes/Samsung PSSD T7/hermes-claw/skills")
PROMOTE_LOG = DATA / "promote.log"


# ── Helpers ────────────────────────────────────────────────────────────────

def _slug(text: str) -> str:
    """Convert title to a safe skill folder name."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")[:48]
    return s or "unnamed-skill"


def _latest_dream_file() -> Path:
    files = sorted(DREAMS_DIR.glob("*.json"), reverse=True)
    if not files:
        raise FileNotFoundError("No dream files found in " + str(DREAMS_DIR))
    return files[0]


def _load_dream(date: str | None) -> tuple[Path, dict]:
    if date:
        f = DREAMS_DIR / f"{date}.json"
        if not f.exists():
            raise FileNotFoundError(f"No dream for {date}")
    else:
        f = _latest_dream_file()
    return f, json.loads(f.read_text())


def _find_card(dream: dict, card_id: str) -> dict | None:
    for card in dream.get("cards", []):
        if card.get("id") == card_id:
            return card
    return None


def _dim_to_category(dim: str) -> str:
    mapping = {
        "repeated-task":    "productivity",
        "skill-gap":        "learning",
        "context-switch":   "workflow",
        "decision":         "reasoning",
        "automation":       "automation",
        "knowledge":        "knowledge",
        "pipeline":         "business",
        "memory":           "memory",
    }
    return mapping.get(dim, "general")


def _generate_skill_md(card: dict, skill_name: str) -> str:
    """Generate a complete Hermes SKILL.md from a dream card."""
    dim = card.get("dim", "unknown")
    trigger = card.get("skill_trigger", "")
    title = card.get("title", skill_name)
    insight = card.get("insight", title)
    action = card.get("action", "Review and act on this pattern")
    priority = card.get("priority", "medium")
    category = _dim_to_category(dim)
    ts = datetime.now().strftime("%Y-%m-%d")
    count_match = re.search(r"(\d+)x", insight)
    occurrence_note = f"Observed {count_match.group(1)} times in recent sessions." if count_match else "Pattern detected in recent sessions."

    # Use trigger phrase as the human-readable description; fall back to title cleanup
    if trigger and len(trigger) > 4:
        clean_title = trigger
    else:
        clean_title = re.sub(r"\(hash:[a-f0-9]+\)", "", title).strip(" —-")
        clean_title = re.sub(r"saw similar prompt \d+x.*", "", clean_title, flags=re.IGNORECASE).strip(" —-")
    if not clean_title or len(clean_title) < 5:
        clean_title = skill_name.replace("-", " ").title()

    # Build trigger phrases from the actual repeated text
    trigger_phrase = f'/{skill_name}' + (f', "{trigger[:50]}"' if trigger else "")

    return f"""---
name: {skill_name}
description: "{clean_title}" — auto-promoted from Dream Engine ({ts}). {occurrence_note}
version: 1.0.0
platforms: [telegram, cli]
metadata:
  hermes:
    category: {category}
    tags: [{dim}, auto-promoted, dream-engine]
    priority: {priority}
    promoted_from: dream-engine
    promoted_date: {ts}
---

# {clean_title[:60]}

**Auto-promoted:** Dream Engine saw this pattern {occurrence_note.lower()}

**Trigger phrases:** {trigger_phrase}

---

## What Bryan Was Doing

> "{clean_title}"

{occurrence_note} This is a `{dim}` pattern — Bryan keeps asking for this same thing.
Time to encode it as a repeatable skill.

**Recommended action:** {action}

---

## When to Use This Skill

Trigger when Bryan:
- Says something like: *"{clean_title[:50]}"*
- Invokes `/{skill_name}`
- Repeats this type of request

---

## Procedure

> **TODO:** Bryan — fill in the actual steps for this workflow.
> The Dream Engine detected the pattern but can't write the procedure.
> What are the steps you follow every time you do this?

1. [ ] Step 1 — describe the first action
2. [ ] Step 2 — describe the next action
3. [ ] Step 3 — describe the output/result

---

## Improvement Notes

- Edit this SKILL.md to add concrete steps.
- Run `hermes memory soul append "I now have a skill for {clean_title}"` to update soul.md.
- After 3 successful uses, revisit and tighten the trigger description.
"""


def _append_promote_log(entry: dict):
    entries = []
    if PROMOTE_LOG.exists():
        try:
            entries = json.loads(PROMOTE_LOG.read_text())
        except Exception:
            entries = []
    entries.append(entry)
    entries = entries[-200:]
    PROMOTE_LOG.write_text(json.dumps(entries, indent=2))


# ── Main ───────────────────────────────────────────────────────────────────

def promote(card_id: str, skill_name: str | None = None, date: str | None = None) -> dict:
    try:
        dream_file, dream = _load_dream(date)
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e)}

    card = _find_card(dream, card_id)
    if not card:
        return {"ok": False, "error": f"Card '{card_id}' not found in dream"}

    if card.get("status") == "promoted":
        existing = card.get("promoted_artifact", "")
        return {"ok": True, "skipped": "already promoted", "artifact": existing}

    # Derive skill name — prefer skill_trigger (actual repeated phrase) over title
    if not skill_name:
        trigger = card.get("skill_trigger", "")
        raw_title = card.get("title", card_id)
        # skill_trigger is the real repeated prompt text — use it
        if trigger and len(trigger) > 4:
            skill_name = _slug(trigger)
        else:
            clean = re.sub(r"\(hash:[a-f0-9]+\)", "", raw_title).strip(" —-")
            # Strip leftover meta-noise from old dream format
            clean = re.sub(r"saw similar prompt \d+x.*", "", clean, flags=re.IGNORECASE).strip(" —-")
            skill_name = _slug(clean) if len(clean) > 4 else _slug(card.get("dim", card_id) + "-" + card_id)

    skill_dir = HERMES_SKILLS / skill_name
    skill_file = skill_dir / "SKILL.md"

    # Don't overwrite an existing real skill
    if skill_file.exists():
        skill_name = skill_name + "-" + card_id
        skill_dir = HERMES_SKILLS / skill_name
        skill_file = skill_dir / "SKILL.md"

    # Write skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_content = _generate_skill_md(card, skill_name)
    skill_file.write_text(skill_content)

    # Mark card promoted
    card["status"] = "promoted"
    card["promoted_artifact"] = str(skill_file)
    card["promoted_ts"] = datetime.now().isoformat()
    dream_file.write_text(json.dumps(dream, indent=2))

    result = {
        "ok": True,
        "skill_name": skill_name,
        "skill_path": str(skill_file),
        "card_id": card_id,
        "promoted_ts": card["promoted_ts"],
    }

    _append_promote_log({
        "ts": result["promoted_ts"],
        "card_id": card_id,
        "skill_name": skill_name,
        "verdict": "shipped",
        "artifact": str(skill_file),
    })

    return result


def main():
    parser = argparse.ArgumentParser(description="Promote a dream card to a Hermes skill")
    parser.add_argument("card_id", help="Dream card ID (e.g. d1, d2, d3)")
    parser.add_argument("--skill-name", help="Override the auto-generated skill name")
    parser.add_argument("--date", help="Dream date YYYY-MM-DD (default: latest)")
    args = parser.parse_args()

    result = promote(args.card_id, skill_name=args.skill_name, date=args.date)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
