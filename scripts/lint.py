"""Vault health checks. Reports issues; does not auto-fix."""
from __future__ import annotations

import argparse
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import frontmatter

REQUIRED_FRONTMATTER_FIELDS = {
    "name",
    "type",
    "tags",
    "source_files",
    "domains",
    "created",
    "updated",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _wiki_pages(vault: Path) -> list[Path]:
    return sorted(
        p
        for p in (vault / "wiki").rglob("*.md")
        if p.name not in {"index.md", "log.md", "hot.md"}
    )


def _wikilinks_in(text: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def find_orphans(vault: Path) -> list[Path]:
    """Pages with zero inbound links from other wiki pages or index.md."""
    pages = _wiki_pages(vault)
    inbound: dict[str, int] = {p.stem: 0 for p in pages}
    sources = list(pages) + [vault / "wiki" / "index.md"]
    for src in sources:
        if not src.exists():
            continue
        for link in _wikilinks_in(src.read_text()):
            tail = link.split("/")[-1].replace(".md", "").strip()
            if tail in inbound and (not hasattr(src, 'stem') or src.stem != tail):
                inbound[tail] += 1
    return [p for p in pages if inbound[p.stem] == 0]


def find_stale(vault: Path, days: int = 90, today: str | None = None) -> list[Path]:
    today_d = date.fromisoformat(today) if today else date.today()
    stale: list[Path] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            continue
        updated = fm.get("updated")
        if isinstance(updated, date):
            updated_d = updated
        elif isinstance(updated, str):
            try:
                updated_d = date.fromisoformat(updated)
            except ValueError:
                continue
        else:
            continue
        if (today_d - updated_d).days > days:
            stale.append(p)
    return stale


def find_broken_links(vault: Path) -> list[dict]:
    pages = _wiki_pages(vault)
    page_stems = {p.stem for p in pages}
    broken: list[dict] = []
    for p in pages:
        for link in _wikilinks_in(p.read_text()):
            target = link.strip()
            if target.startswith("../"):
                resolved = (p.parent / target).resolve()
                if not resolved.exists() and not (resolved.parent / f"{resolved.name}.md").exists():
                    broken.append({"page": str(p), "target": target})
            else:
                tail = target.split("/")[-1].replace(".md", "")
                if tail not in page_stems and target not in {"index", "log", "hot"}:
                    broken.append({"page": str(p), "target": target})
    return broken


def find_missing_frontmatter(vault: Path) -> list[dict]:
    out: list[dict] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            out.append({"path": str(p), "missing": sorted(REQUIRED_FRONTMATTER_FIELDS)})
            continue
        present = set(fm.metadata.keys())
        missing = REQUIRED_FRONTMATTER_FIELDS - present
        if missing:
            out.append({"path": str(p), "missing": sorted(missing)})
    return out


def find_raw_backlog(vault: Path, max_age_days: int = 7) -> list[dict]:
    raw_dir = vault / "raw"
    if not raw_dir.exists():
        return []
    now = datetime.now().timestamp()
    cutoff = now - max_age_days * 86400
    backlog: list[dict] = []
    for p in raw_dir.iterdir():
        if p.is_dir():
            continue
        if p.name.startswith(".") or p.name == ".gitkeep":
            continue
        if p.stat().st_mtime < cutoff:
            age_days = int((now - p.stat().st_mtime) / 86400)
            backlog.append({"path": str(p), "age_days": age_days})
    return backlog


def find_unassigned_domain(vault: Path) -> list[Path]:
    out: list[Path] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            continue
        domains = fm.get("domains") or []
        if "unassigned" in domains:
            out.append(p)
    return out


def lint_vault(vault: Path, today: str | None = None) -> dict:
    report = {
        "orphans": [str(p) for p in find_orphans(vault)],
        "stale": [str(p) for p in find_stale(vault, today=today)],
        "broken_links": find_broken_links(vault),
        "missing_frontmatter": find_missing_frontmatter(vault),
        "raw_backlog": find_raw_backlog(vault),
        "unassigned_domain": [str(p) for p in find_unassigned_domain(vault)],
    }
    report["total_issues"] = sum(
        len(v) if isinstance(v, list) else 0 for v in report.values()
    )
    return report


def format_report(report: dict, today: str) -> str:
    lines = [f"# Vault Lint Report\n\nDate: {today}\nIssues: {report['total_issues']}\n"]
    for key, label in [
        ("orphans", "Orphans"),
        ("stale", "Stale"),
        ("broken_links", "Broken links"),
        ("missing_frontmatter", "Missing frontmatter"),
        ("raw_backlog", "Raw backlog"),
        ("unassigned_domain", "Unassigned domain"),
    ]:
        items = report[key]
        lines.append(f"\n## {label} ({len(items)})\n")
        for item in items:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault",
        default="/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master",
    )
    parser.add_argument(
        "--out",
        default="/Volumes/Samsung PSSD T7/AIS-OS/dashboard/lint-report.md",
    )
    args = parser.parse_args()
    vault = Path(args.vault)
    today = date.today().isoformat()
    report = lint_vault(vault, today=today)
    Path(args.out).write_text(format_report(report, today))
    print(f"Lint complete. {report['total_issues']} issues. Report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
