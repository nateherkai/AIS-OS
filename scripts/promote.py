"""Promote a dream card to an installed artifact (skill / hook / memory / cron / doc).

Closes the dream -> task -> skill loop. Pipeline:
  1. Resolve card by id across `dashboard/data/dreams/*.json` (newest first).
  2. Infer artifact kind from card dim if --as not given.
  3. Draft artifact from `templates/skill.md.tmpl` (skill kind only for now).
  4. Smoke-test the draft (yaml frontmatter parses, name/description non-empty).
  5. Install to `~/.claude/skills/<name>/` on pass, or `~/.claude/skills/_quarantine/<name>/`
     with a `smoke.json` report on fail.
  6. Append verdict to `dashboard/data/promote.log` (newline-delimited JSON).
  7. Mark card status="promoted" + record artifact path in source dream file.

Usage:
  python3 -m scripts.promote <card-id> [--as skill|memory|hook|cron|doc] [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AISOS_ROOT = Path(__file__).resolve().parent.parent
DREAMS_DIR = AISOS_ROOT / "dashboard" / "data" / "dreams"
PROMOTE_LOG = AISOS_ROOT / "dashboard" / "data" / "promote.log"
TEMPLATES_DIR = AISOS_ROOT / "templates"
SKILLS_INSTALL_DIR = Path.home() / ".claude" / "skills"
QUARANTINE_DIR = SKILLS_INSTALL_DIR / "_quarantine"

DIM_TO_KIND = {
    "repeated-task": "skill",
    "workflow": "skill",
    "skill-perf": "skill",
    "memory-health": "memory",
    "session-hygiene": "hook",
    "cost": "doc",
    "external-opps": "doc",
    "business-context": "memory",
}


@dataclass
class ResolvedCard:
    card: dict[str, Any]
    source_path: Path
    dream_date: str
    generated_at: str


def slugify(text: str, max_len: int = 50) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-+", "-", text)
    return text[:max_len].rstrip("-") or "promoted-skill"


def resolve_card(card_id: str) -> ResolvedCard:
    files = sorted(DREAMS_DIR.glob("*.json"), reverse=True)
    if not files:
        raise FileNotFoundError(f"no dream files in {DREAMS_DIR}")
    for path in files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        cards = data.get("cards", [])
        for c in cards:
            if c.get("id") == card_id:
                return ResolvedCard(
                    card=c,
                    source_path=path,
                    dream_date=data.get("date", path.stem),
                    generated_at=data.get("generated_at", ""),
                )
    raise LookupError(f"card id {card_id!r} not found in any dream file")


def infer_kind(card: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    return DIM_TO_KIND.get(card.get("dim", ""), "skill")


def render_skill(rc: ResolvedCard, name: str) -> str:
    tmpl = (TEMPLATES_DIR / "skill.md.tmpl").read_text()
    c = rc.card
    description = (c.get("insight") or c.get("title") or "Auto-promoted skill.").strip().rstrip(".") + "."
    trigger = c.get("title", name).strip().lower()
    repl = {
        "{{name}}": name,
        "{{description}}": description,
        "{{trigger_phrase}}": trigger[:60],
        "{{title}}": c.get("title", name),
        "{{card_id}}": c.get("id", ""),
        "{{dim}}": c.get("dim", ""),
        "{{generated_at}}": rc.generated_at,
        "{{insight}}": c.get("insight", ""),
        "{{action}}": c.get("action", ""),
        "{{dream_date}}": rc.dream_date,
        "{{estimated_value_minutes}}": str(c.get("estimated_value_minutes", "")),
    }
    out = tmpl
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def smoke_test_skill(rendered: str) -> tuple[bool, dict[str, Any]]:
    """Validate skill markdown. Returns (passed, report)."""
    report: dict[str, Any] = {"checks": []}
    ok = True

    if not rendered.startswith("---\n"):
        ok = False
        report["checks"].append({"name": "frontmatter_open", "ok": False})
    else:
        report["checks"].append({"name": "frontmatter_open", "ok": True})

    end_idx = rendered.find("\n---\n", 4)
    if end_idx == -1:
        ok = False
        report["checks"].append({"name": "frontmatter_close", "ok": False})
        return ok, report
    report["checks"].append({"name": "frontmatter_close", "ok": True})

    front = rendered[4:end_idx]
    has_name = bool(re.search(r"^name:\s*\S+", front, re.M))
    has_desc = bool(re.search(r"^description:\s*\S+", front, re.M))
    report["checks"].append({"name": "has_name", "ok": has_name})
    report["checks"].append({"name": "has_description", "ok": has_desc})
    if not (has_name and has_desc):
        ok = False

    leftover = re.findall(r"\{\{[^}]+\}\}", rendered)
    report["checks"].append({"name": "no_unfilled_templates", "ok": not leftover, "leftover": leftover})
    if leftover:
        ok = False

    todo_count = rendered.count("[TODO")
    report["todo_count"] = todo_count
    report["checks"].append({"name": "todo_count_logged", "ok": True})

    return ok, report


def install_skill(name: str, rendered: str, passed: bool, smoke_report: dict[str, Any]) -> Path:
    target_root = SKILLS_INSTALL_DIR if passed else QUARANTINE_DIR
    target_dir = target_root / name
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "SKILL.md").write_text(rendered)
    if not passed:
        (target_dir / "smoke.json").write_text(json.dumps(smoke_report, indent=2))
    return target_dir / "SKILL.md"


def log_verdict(card_id: str, verdict: str, artifact: Path | None, summary: str) -> None:
    PROMOTE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "card_id": card_id,
        "verdict": verdict,
        "artifact_path": str(artifact) if artifact else None,
        "summary": summary,
    }
    with PROMOTE_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def mark_card_promoted(rc: ResolvedCard, artifact: Path, verdict: str) -> None:
    data = json.loads(rc.source_path.read_text())
    for c in data.get("cards", []):
        if c.get("id") == rc.card.get("id"):
            c["status"] = "promoted" if verdict == "shipped" else "quarantined"
            c["promoted_artifact"] = str(artifact)
            c["promoted_at"] = datetime.now(timezone.utc).isoformat()
            c["promote_verdict"] = verdict
    rc.source_path.write_text(json.dumps(data, indent=2))


def promote(card_id: str, kind_override: str | None, force: bool) -> int:
    try:
        rc = resolve_card(card_id)
    except (FileNotFoundError, LookupError) as e:
        log_verdict(card_id, "error", None, str(e))
        print(f"error: {e}", file=sys.stderr)
        return 2

    card = rc.card
    if card.get("status") == "promoted" and not force:
        msg = f"card {card_id} already promoted to {card.get('promoted_artifact')}; pass --force to re-run"
        log_verdict(card_id, "skipped", None, msg)
        print(msg)
        return 0

    kind = infer_kind(card, kind_override)
    if kind != "skill":
        msg = f"kind={kind!r} not yet supported by promote.py (only skill). Card: {card.get('title')}"
        log_verdict(card_id, "needs-fix", None, msg)
        print(msg)
        return 3

    name = slugify(card.get("title", card_id))
    rendered = render_skill(rc, name)
    passed, smoke_report = smoke_test_skill(rendered)
    artifact = install_skill(name, rendered, passed, smoke_report)

    verdict = "shipped" if passed else "needs-fix"
    summary = f"{verdict} kind={kind} name={name} todos={smoke_report.get('todo_count', 0)}"
    log_verdict(card_id, verdict, artifact, summary)
    mark_card_promoted(rc, artifact, verdict)

    print(f"{verdict}: {artifact}")
    if not passed:
        print(f"  smoke checks failed; see {artifact.parent / 'smoke.json'}")
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote a dream card to an installed artifact.")
    parser.add_argument("card_id", help="Card id (e.g. d1) from a dream file in dashboard/data/dreams/")
    parser.add_argument("--as", dest="kind", choices=["skill", "memory", "hook", "cron", "doc"], default=None)
    parser.add_argument("--force", action="store_true", help="Re-promote even if card already promoted.")
    args = parser.parse_args(argv)
    return promote(args.card_id, args.kind, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
