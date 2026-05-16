"""
wiki_reader.py — Tree/page/search helpers for the Wiki Browser (N2).
Parses YAML frontmatter, computes backlinks, returns structured data.
All path arguments are validated against WIKI_ROOT to prevent traversal.
"""

import os
import re
import json
from pathlib import Path

# ── Vault roots ──────────────────────────────────────────────────
VAULT = Path(__file__).parent.parent.parent / "Bryan-Aaron-Master"
WIKI_ROOT = VAULT / "wiki"
DOMAIN_ROOTS = {
    f"{d.name}": d
    for d in sorted(VAULT.iterdir())
    if d.is_dir() and re.match(r"^\d{2}-", d.name)
}

# ── Path safety ───────────────────────────────────────────────────

def _safe_resolve(base: Path, rel: str) -> Path:
    """Resolve rel against base; raise ValueError if traversal escapes base."""
    candidate = (base / rel).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        raise ValueError(f"Path traversal rejected: {rel}")
    return candidate


# ── Frontmatter parser ────────────────────────────────────────────

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is parsed from YAML-lite."""
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    fm: dict = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # Handle list literals: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            fm[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        else:
            fm[key] = val.strip("'\"")
    return fm, body


# ── Backlinks ─────────────────────────────────────────────────────

def _find_backlinks(target_stem: str) -> list[dict]:
    """Find all wiki pages that contain [[target_stem]] in their body."""
    pattern = re.compile(r"\[\[" + re.escape(target_stem) + r"\]\]", re.IGNORECASE)
    results = []
    for md in WIKI_ROOT.rglob("*.md"):
        try:
            text = md.read_text(errors="replace")
        except Exception:
            continue
        if pattern.search(text):
            _, body = _parse_frontmatter(text)
            if target_stem not in md.stem:  # skip self
                rel = str(md.relative_to(WIKI_ROOT))
                results.append({"path": rel, "label": md.stem})
    return results


def _extract_outbound(body: str) -> list[dict]:
    """Extract [[links]] from a markdown body."""
    found = re.findall(r"\[\[([^\]]+)\]\]", body)
    seen = set()
    out = []
    for ref in found:
        if ref not in seen:
            seen.add(ref)
            out.append({"path": ref + ".md", "label": ref})
    return out


# ── Tree ──────────────────────────────────────────────────────────

def tree() -> dict:
    """Return nested tree of wiki dirs + domain folders."""

    def _scan_dir(d: Path, base: Path) -> list[dict]:
        entries = []
        try:
            items = sorted(d.iterdir())
        except PermissionError:
            return entries
        for item in items:
            if item.name.startswith("."):
                continue
            if item.is_dir():
                children = _scan_dir(item, base)
                if children:
                    rel = str(item.relative_to(base))
                    entries.append({"type": "dir", "name": item.name, "path": rel, "children": children})
            elif item.suffix == ".md":
                rel = str(item.relative_to(base))
                entries.append({"type": "file", "name": item.stem, "path": rel})
        return entries

    wiki_tree = []
    # Top-level wiki files first
    for f in sorted(WIKI_ROOT.glob("*.md")):
        wiki_tree.append({"type": "file", "name": f.stem, "path": f.name})
    # Wiki subdirs
    for d in sorted(WIKI_ROOT.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            children = _scan_dir(d, WIKI_ROOT)
            if children:
                wiki_tree.append({"type": "dir", "name": d.name, "path": d.name, "children": children})

    domain_tree = []
    for name, dpath in DOMAIN_ROOTS.items():
        children = _scan_dir(dpath, dpath)
        domain_tree.append({
            "type": "dir",
            "name": name,
            "path": name,
            "children": children,
            "is_domain": True,
        })

    return {"wiki": wiki_tree, "domains": domain_tree}


# ── Page ──────────────────────────────────────────────────────────

def page(rel_path: str) -> dict:
    """
    Load a wiki or domain page.
    rel_path examples:
      "concepts/foo.md"         → wiki page
      "01-AG-COACH-PRO/bar.md"  → domain page
    """
    # Determine which root to use
    if any(rel_path.startswith(k + "/") or rel_path == k for k in DOMAIN_ROOTS):
        # Domain page — root is VAULT, but validate within VAULT
        base = VAULT
        safe = _safe_resolve(base, rel_path)
    else:
        base = WIKI_ROOT
        safe = _safe_resolve(base, rel_path)

    if not safe.exists():
        raise FileNotFoundError(f"Page not found: {rel_path}")

    text = safe.read_text(errors="replace")
    fm, body = _parse_frontmatter(text)

    stem = safe.stem
    backlinks = _find_backlinks(stem)
    outbound = _extract_outbound(body)

    return {
        "path": rel_path,
        "stem": stem,
        "frontmatter": fm,
        "body": body,
        "backlinks": backlinks,
        "outbound": outbound,
    }


# ── Search ────────────────────────────────────────────────────────

def search(q: str) -> list[dict]:
    """
    Fuzzy search wiki + domain pages.
    Returns [{path, label, snippet, score}] sorted by relevance.
    """
    if not q or len(q) < 2:
        return []
    q_low = q.lower()
    results = []

    def _search_dir(root: Path, base: Path, is_domain: bool = False):
        for md in root.rglob("*.md"):
            try:
                text = md.read_text(errors="replace")
            except Exception:
                continue
            stem = md.stem
            rel = str(md.relative_to(base))
            stem_low = stem.lower()
            score = 0
            if q_low == stem_low:
                score = 100
            elif stem_low.startswith(q_low):
                score = 80
            elif q_low in stem_low:
                score = 60

            # grep first 200 chars of body
            _, body = _parse_frontmatter(text)
            body_snippet = body[:400]
            if q_low in body_snippet.lower():
                score = max(score, 40)
            elif q_low in body.lower():
                score = max(score, 20)

            if score > 0:
                # Extract snippet around match
                idx = body.lower().find(q_low)
                if idx >= 0:
                    start = max(0, idx - 40)
                    end = min(len(body), idx + 120)
                    snippet = body[start:end].replace("\n", " ").strip()
                else:
                    snippet = body[:120].replace("\n", " ").strip()

                results.append({
                    "path": rel,
                    "label": stem,
                    "snippet": snippet,
                    "score": score,
                    "is_domain": is_domain,
                })

    _search_dir(WIKI_ROOT, WIKI_ROOT, is_domain=False)
    for name, dpath in DOMAIN_ROOTS.items():
        _search_dir(dpath, dpath, is_domain=True)

    results.sort(key=lambda x: -x["score"])
    return results[:30]
