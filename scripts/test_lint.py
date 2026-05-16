"""Tests for vault lint script."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from scripts.lint import (
    find_orphans,
    find_stale,
    find_broken_links,
    find_missing_frontmatter,
    find_raw_backlog,
    lint_vault,
)


def _setup_vault(tmp: Path) -> Path:
    """Build minimal vault fixture."""
    (tmp / "raw").mkdir()
    (tmp / "raw" / "_ingested").mkdir()
    (tmp / "wiki").mkdir()
    for sub in ["sources", "people", "concepts"]:
        (tmp / "wiki" / sub).mkdir()
    (tmp / "wiki" / "index.md").write_text(
        "# Wiki Index\n\n- [[concepts/connected]]\n"
    )
    (tmp / "wiki" / "log.md").write_text("# Log\n")
    (tmp / "wiki" / "hot.md").write_text("# Hot\n")
    return tmp


def test_find_orphans_detects_unlinked_page(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "connected.md").write_text(
        "---\nname: connected\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Connected\n[[orphan]]\n"
    )
    (vault / "wiki" / "concepts" / "orphan.md").write_text(
        "---\nname: orphan\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Orphan\nno links out\n"
    )
    orphans = find_orphans(vault)
    # connected has no inbound links (only index points there but index is excluded? actually index DOES point — so connected has 1 inbound, orphan has 1 inbound from connected).
    # Re-thinking: index.md links to connected. connected links to orphan. So both have inbound. find_orphans excludes index from being a source? Implementation choice: index COUNTS as a source.
    # With both linked, neither is orphan. Test must construct an actual orphan.
    # Fix: add a third page with no inbound at all.
    (vault / "wiki" / "concepts" / "truly_orphan.md").write_text(
        "---\nname: truly_orphan\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Truly Orphan\n[[connected]]\n"
    )
    orphans2 = find_orphans(vault)
    assert any("truly_orphan.md" in str(o) for o in orphans2)


def test_find_stale_flags_old_updated(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "old.md").write_text(
        "---\nname: old\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2025-01-01\nupdated: 2025-01-01\n---\n# Old\n[[connected]]\n"
    )
    stale = find_stale(vault, days=90, today="2026-05-16")
    assert len(stale) == 1
    assert "old.md" in str(stale[0])


def test_find_broken_links_detects_missing_target(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "src.md").write_text(
        "---\nname: src\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Src\n[[missing-target]]\n"
    )
    broken = find_broken_links(vault)
    assert any("missing-target" in b["target"] for b in broken)


def test_find_missing_frontmatter(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "bad.md").write_text("# Bad\nno frontmatter\n")
    missing = find_missing_frontmatter(vault)
    assert any("bad.md" in str(m["path"]) for m in missing)


def test_find_raw_backlog_old_files(tmp_path):
    vault = _setup_vault(tmp_path)
    old_file = vault / "raw" / "old.md"
    old_file.write_text("old")
    import time
    ten_days_ago = time.time() - 10 * 86400
    os.utime(old_file, (ten_days_ago, ten_days_ago))
    backlog = find_raw_backlog(vault, max_age_days=7)
    assert any("old.md" in str(b["path"]) for b in backlog)


def test_lint_vault_returns_full_report(tmp_path):
    vault = _setup_vault(tmp_path)
    report = lint_vault(vault, today="2026-05-16")
    for key in ["orphans", "stale", "broken_links", "missing_frontmatter", "raw_backlog", "parse_errors", "total_issues"]:
        assert key in report
