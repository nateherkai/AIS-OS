#!/usr/bin/env python3
"""capabilities-health — a deterministic structural census of an AIOS Capability layer.

Drop-in lint for any Claude Code AIOS (the AIS-OS starter kit and anything grown from
it). It is the deterministic floor under the **Capabilities** C of `/audit`: `/audit`
*scores* whether your skills are in good shape; this *proves* it, item by item, and
never guesses. A REPORTER, not a janitor — it never rewrites a SKILL.md or your index.

Why it exists: a fast-growing skill folder outruns its own documentation. You add
skills faster than you update the README/index that lists them, and within a month the
map that's supposed to tell you what you own is lying. This catches that drift the
moment it appears, so the Capabilities layer stays legible as it grows. (It's the
3Ms Operate layer — Bike Method, Kill Switch — turned into a tool: keep what earns its
place, see what's drifting, retire what doesn't.)

Six sections, each degrades gracefully if a layer is absent (no scripts/, no knowledge/,
no index file — all fine):

  1. Census drift  — skill/page counts claimed in your index (CAPABILITIES.md or
                     README.md) vs what's actually on disk. The headline number.
  2. Undocumented  — skills on disk whose name never appears in the index (you own it,
                     the map doesn't list it).
  3. Phantom       — `/name` skill refs in the index with no skill dir on disk.
  4. Broken refs   — `scripts/<file>` and `/skill` references that point at nothing.
  5. Frontmatter   — each SKILL.md opens with `---` frontmatter carrying `name:` +
                     `description:`; `name:` should match its directory.
  6. Orphan scripts— scripts/ files referenced by no skill / index / CLAUDE.md.

    python3 capabilities-health.py                 # run from your AIOS root
    python3 capabilities-health.py --root PATH      # or point at it
    python3 capabilities-health.py --index README.md
    python3 capabilities-health.py --section drift  # one section only

Stdlib only. No deps, no network, no writes. Pairs with the /capabilities-health skill
(the AI layer: regenerate the index, retire-vs-keep calls). MIT-friendly to reuse.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

# Slash-names that are Claude Code built-ins / common harness commands, NOT kit skills —
# so a `/name` ref to one of these is never a "phantom" or "broken" skill.
BUILTINS = {
    "loop", "schedule", "code-review", "review", "security-review", "init",
    "run", "verify", "simplify", "config", "help", "clear", "compact",
}

# Generic doc placeholders that look like a /command but never name a real skill
# (e.g. "invoke with `/name`", "`/the-slash-command`"). Filtered from ref checks.
PLACEHOLDERS = {"name", "the-slash-command", "your-skill", "skill-name", "x", "foo"}

SECTIONS = ["drift", "undocumented", "phantom", "brokenrefs", "frontmatter", "orphans"]


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def find_index(root, override):
    """The human index that lists the skills. Override, else CAPABILITIES.md, else README.md."""
    if override:
        return override, read(os.path.join(root, override))
    for name in ("CAPABILITIES.md", "README.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            return name, read(p)
    return None, ""


def disk_skills(skills_dir):
    """Skill dirs that actually carry a SKILL.md."""
    out = {}
    if not os.path.isdir(skills_dir):
        return out
    for name in sorted(os.listdir(skills_dir)):
        sk = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.isfile(sk):
            out[name] = sk
    return out


def disk_scripts(scripts_dir):
    out = {}
    if not os.path.isdir(scripts_dir):
        return out
    for name in sorted(os.listdir(scripts_dir)):
        p = os.path.join(scripts_dir, name)
        if os.path.isfile(p) and name.endswith((".sh", ".py")):
            out[name] = p
    return out


def parse_frontmatter_name(text):
    """Return (name, has_frontmatter, has_description) from a SKILL.md's leading --- block."""
    if not text.startswith("---"):
        return None, False, False
    end = text.find("\n---", 3)
    if end == -1:
        return None, False, False
    block = text[3:end]
    name = None
    has_desc = False
    for line in block.splitlines():
        m = re.match(r"\s*name:\s*(\S+)", line)
        if m:
            name = m.group(1).strip()
        if re.match(r"\s*description:\s*\S", line):
            has_desc = True
    return name, True, has_desc


def h(title):
    print(f"\n{'=' * 4} {title} {'=' * 4}")


def run(root, index_override, want):
    skills_dir = os.path.join(root, ".claude", "skills")
    scripts_dir = os.path.join(root, "scripts")
    index_name, index = find_index(root, index_override)

    skills = disk_skills(skills_dir)
    scripts = disk_scripts(scripts_dir)
    pages_dir = os.path.join(root, "knowledge", "pages")
    pages = [f for f in os.listdir(pages_dir) if f.endswith(".md")] if os.path.isdir(pages_dir) else []

    if not skills:
        print(f"No skills found under {skills_dir} — is --root pointing at your AIOS root?")
        return 0
    if index_name is None:
        print("Note: no CAPABILITIES.md or README.md index found — index-dependent sections skipped.\n")

    findings = 0

    # --- 1. Census drift ---------------------------------------------------
    if want in (None, "drift"):
        h(f"1. CENSUS DRIFT (vs {index_name or 'no index'})")
        if index_name is None:
            print("  skipped — no index file to compare against")
        else:
            m = re.search(r"[Ss]kills\s*\((\d+)\)", index) or re.search(r"(\d+)\s+skills", index)
            claimed_skills = int(m.group(1)) if m else None
            m = re.search(r"(\d+)\s*pages", index)
            claimed_pages = int(m.group(1)) if m else None

            def line(label, claimed, actual):
                nonlocal findings
                if claimed is None:
                    print(f"  {label:14} disk={actual:<5} (no count claimed in {index_name})")
                elif claimed != actual:
                    findings += 1
                    print(f"  {label:14} disk={actual:<5} claimed={claimed:<5} DRIFT ({actual - claimed:+d})")
                else:
                    print(f"  {label:14} disk={actual:<5} claimed={claimed:<5} ok")

            line("skills", claimed_skills, len(skills))
            if pages:
                line("knowledge pp", claimed_pages, len(pages))
        if scripts:
            print(f"  {'scripts':14} disk={len(scripts):<5} (informational)")

    # --- 2. Undocumented skills -------------------------------------------
    if want in (None, "undocumented"):
        h("2. UNDOCUMENTED SKILLS (on disk, absent from the index)")
        if index_name is None:
            print("  skipped — no index file")
        else:
            missing = [n for n in skills if not re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", index)]
            if missing:
                findings += len(missing)
                for n in missing:
                    print(f"  + {n}")
            else:
                print("  (none — every disk skill is named in the index)")

    # --- 3. Phantom skill refs --------------------------------------------
    if want in (None, "phantom"):
        h("3. PHANTOM SKILL REFS (in the index, no skill dir on disk)")
        if index_name is None:
            print("  skipped — no index file")
        else:
            refs = set(re.findall(r"`/([a-z][a-z0-9-]+)`", index))
            phantom = sorted(r for r in refs if r not in skills and r not in BUILTINS and r not in PLACEHOLDERS)
            if phantom:
                findings += len(phantom)
                for r in phantom:
                    print(f"  ? /{r}")
            else:
                print("  (none — every /skill in the index resolves to a dir)")

    # --- 4. Broken references ---------------------------------------------
    # A script ref resolves if the file exists at root scripts/ OR in the referencing
    # skill's own scripts/ subdir. `(?<!\./)` skips illustrative `./scripts/x` shell
    # examples; canonical refs are written `scripts/x`. Cross-skill /name refs are only
    # checked in the curated docs (index + CLAUDE.md) — skill bodies are full of example
    # slash-tokens, so flagging them there is noise.
    if want in (None, "brokenrefs"):
        h("4. BROKEN REFERENCES (scripts/ files + /skill refs in curated docs)")
        broken = []

        def script_resolves(sref, local_dir):
            if os.path.isfile(os.path.join(scripts_dir, sref)):
                return True
            base = sref.split("/", 1)[-1]
            return local_dir is not None and (
                os.path.isfile(os.path.join(local_dir, "scripts", sref))
                or os.path.isfile(os.path.join(local_dir, "scripts", base))
            )

        claude_md = read(os.path.join(root, "CLAUDE.md"))
        sources = [("index", index, None), ("CLAUDE.md", claude_md, None)]
        for n, p in skills.items():
            sources.append((f"skills/{n}", read(p), os.path.dirname(p)))
        for origin, text, local in sources:
            for sref in set(re.findall(r"(?<!\./)\bscripts/([\w./-]+\.(?:sh|py))", text)):
                if not script_resolves(sref, local):
                    broken.append((origin, f"scripts/{sref}"))
        for origin, text in [("index", index), ("CLAUDE.md", claude_md)]:
            for sk in set(re.findall(r"`/([a-z][a-z0-9-]+)`", text)):
                if sk not in skills and sk not in BUILTINS and sk not in PLACEHOLDERS:
                    broken.append((origin, f"/{sk}"))
        if broken:
            findings += len(broken)
            for origin, ref in sorted(set(broken)):
                print(f"  x {ref:34} referenced in {origin}")
        else:
            print("  (none — all scripts/ files and curated-doc /skill refs resolve)")

    # --- 5. Frontmatter ----------------------------------------------------
    if want in (None, "frontmatter"):
        h("5. FRONTMATTER (name/description present, name matches dir)")
        bad = []
        for n, p in skills.items():
            name, has_fm, has_desc = parse_frontmatter_name(read(p))
            if not has_fm:
                bad.append(f"  ! {n}: no --- frontmatter block")
            elif name is None:
                bad.append(f"  ! {n}: frontmatter missing `name:`")
            elif name != n:
                bad.append(f"  ! {n}: name: '{name}' != dir '{n}'")
            elif not has_desc:
                bad.append(f"  ! {n}: frontmatter missing `description:`")
        if bad:
            findings += len(bad)
            print("\n".join(bad))
        else:
            print("  (none — all skills have valid name/description frontmatter)")

    # --- 6. Orphan scripts -------------------------------------------------
    if want in (None, "orphans"):
        h("6. ORPHAN SCRIPTS (in scripts/, referenced by nothing)")
        if not scripts:
            print("  (no scripts/ dir — skipped)")
        else:
            blob = index + read(os.path.join(root, "CLAUDE.md"))
            for p in skills.values():
                blob += read(p)
            for sp in scripts.values():
                blob += read(sp)
            orphans = [n for n in scripts if n not in blob]
            if orphans:
                findings += len(orphans)
                for n in orphans:
                    print(f"  . {n}")
            else:
                print("  (none — every script is referenced somewhere)")

    print(f"\n{'=' * 30}\nTotal flagged items: {findings}")
    return findings


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.getcwd(), help="AIOS root (default: current directory)")
    ap.add_argument("--index", default=None, help="index file to check (default: CAPABILITIES.md, else README.md)")
    ap.add_argument("--section", choices=SECTIONS, default=None, help="run one section only (default: all)")
    args = ap.parse_args()
    run(args.root, args.index, args.section)
    sys.exit(0)  # always exit 0 — it's a reporter, not a gate
