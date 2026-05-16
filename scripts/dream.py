"""Dream engine — 8-dim nightly pass over Bryan's AI stack."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore


VAULT_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
AISOS_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS")
DREAMS_DIR_DEFAULT = AISOS_DEFAULT / "dashboard" / "data" / "dreams"

DIMENSIONS = [
    "conversation",
    "cost",
    "skill-perf",
    "memory-health",
    "session-hygiene",
    "workflow",
    "external-opps",
    "business-context",
]


@dataclass
class Card:
    id: str
    dim: str
    title: str
    insight: str
    action: str
    estimated_value_minutes: int
    status: str  # open | done | dismissed


@dataclass
class DreamConfig:
    max_cards: int = 4
    lookback_days: int = 7
    model: str = "claude-opus-4-7"
    vault: Path = field(default_factory=lambda: VAULT_DEFAULT)
    aisos: Path = field(default_factory=lambda: AISOS_DEFAULT)
    dreams_dir: Path = field(default_factory=lambda: DREAMS_DIR_DEFAULT)


def validate_cards(cards: list[Card]) -> None:
    if len(cards) > 4:
        raise ValueError("max 4 cards")
    seen_ids: set[str] = set()
    for c in cards:
        if c.id in seen_ids:
            raise ValueError(f"duplicate card id: {c.id}")
        seen_ids.add(c.id)
        if c.dim not in DIMENSIONS:
            raise ValueError(f"invalid dim: {c.dim}")
        if c.status not in {"open", "done", "dismissed"}:
            raise ValueError(f"invalid status: {c.status}")


def build_card_json(
    cards: list[Card], summary: str, date: str, next_run: str
) -> str:
    payload = {
        "date": date,
        "cards": [asdict(c) for c in cards],
        "summary": summary,
        "next_run": next_run,
    }
    return json.dumps(payload, indent=2)


def write_dream_output(
    cards: list[Card],
    out_dir: Path,
    summary: str,
    date: str,
    next_run: str,
) -> Path:
    validate_cards(cards)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}.json"
    path.write_text(build_card_json(cards, summary, date, next_run))
    return path


def gather_context(cfg: DreamConfig) -> dict[str, str]:
    """Collect compact context for each dim. Read sparingly — keep token cost low."""
    ctx: dict[str, str] = {}
    hot = cfg.vault / "wiki" / "hot.md"
    log = cfg.vault / "wiki" / "log.md"
    ctx["vault_hot"] = hot.read_text()[:600] if hot.exists() else ""
    ctx["vault_log_tail"] = (
        "\n".join(log.read_text().splitlines()[-20:]) if log.exists() else ""
    )
    bb = cfg.vault / "Business_Brain.md"
    ctx["business_brain"] = bb.read_text()[:2000] if bb.exists() else ""
    try:
        import subprocess
        ctx["git_recent"] = subprocess.check_output(
            ["git", "log", "--oneline", "-20"], cwd=cfg.aisos, text=True
        )
    except Exception:
        ctx["git_recent"] = ""
    skills_dir = Path.home() / ".claude" / "skills"
    if skills_dir.exists():
        ctx["skills_list"] = "\n".join(sorted(p.name for p in skills_dir.iterdir() if p.is_dir()))
    else:
        ctx["skills_list"] = ""
    return ctx


def build_prompt(ctx: dict[str, str], cfg: DreamConfig) -> str:
    today = date.today().isoformat()
    return f"""You are Bryan's nightly dream engine. Today is {today}. Generate up to {cfg.max_cards} high-leverage recommendations across the 8 dimensions: {", ".join(DIMENSIONS)}.

CONTEXT:

[vault_hot]
{ctx['vault_hot']}

[vault_log_tail]
{ctx['vault_log_tail']}

[business_brain (truncated)]
{ctx['business_brain']}

[git_recent]
{ctx['git_recent']}

[skills_installed]
{ctx['skills_list']}

REQUIREMENTS:
- Max {cfg.max_cards} cards. Fewer is fine if leverage isn't there. Don't pad.
- Each card MUST be specific + actionable + tied to Bryan's Q-goals (50 schools by Aug 2026, $120K/yr, Ag Coach Pro focus).
- Each card has: id (d1..d{cfg.max_cards}), dim (one of {DIMENSIONS}), title (≤80 chars), insight (1-2 sentences), action (imperative, ≤120 chars), estimated_value_minutes (int).
- Output ONLY valid JSON matching this schema:

{{
  "summary": "1-line dream summary",
  "cards": [
    {{"id": "d1", "dim": "skill-perf", "title": "...", "insight": "...", "action": "...", "estimated_value_minutes": 45}}
  ]
}}
"""


def call_claude(prompt: str, cfg: DreamConfig) -> dict:
    if Anthropic is None:
        raise RuntimeError("anthropic SDK not installed. pip install anthropic")
    client = Anthropic()
    msg = client.messages.create(
        model=cfg.model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default=str(VAULT_DEFAULT))
    parser.add_argument("--out-dir", default=str(DREAMS_DIR_DEFAULT))
    parser.add_argument("--dry-run", action="store_true", help="Skip Claude API call; emit empty card set.")
    args = parser.parse_args()

    cfg = DreamConfig(vault=Path(args.vault), dreams_dir=Path(args.out_dir))
    ctx = gather_context(cfg)
    today = date.today().isoformat()
    next_run = (datetime.now() + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0).isoformat()

    if args.dry_run:
        cards: list[Card] = []
        summary = "Dry-run dream pass — no cards generated."
    else:
        prompt = build_prompt(ctx, cfg)
        result = call_claude(prompt, cfg)
        cards = [Card(status="open", **c) for c in result.get("cards", [])]
        summary = result.get("summary", "")

    path = write_dream_output(cards, cfg.dreams_dir, summary, today, next_run)
    print(f"Dream pass complete. Cards: {len(cards)}. Output: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
