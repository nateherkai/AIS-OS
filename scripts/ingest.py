"""CLI wrapper for ingest skill. Lists raw/ files; actual ingest happens via Claude Code skill. Merge-only policy enforced by `assert_no_overwrite` for any programmatic ingest."""
from __future__ import annotations

import argparse
from pathlib import Path

VAULT_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")


class WikiOverwriteError(RuntimeError):
    """Raised when an ingest attempts to overwrite an existing wiki page wholesale."""


def assert_no_overwrite(wiki_page: Path) -> None:
    """Guard against wholesale overwrites of existing wiki pages. Merge-only policy.

    Call this from any future programmatic ingest before writing a wiki page.
    The Claude-Code ingest skill must also honor this rule (it is documented in
    ~/.claude/skills/ingest/SKILL.md).
    """
    if wiki_page.exists():
        raise WikiOverwriteError(
            f"Refusing to overwrite existing wiki page: {wiki_page}. "
            f"Ingest is merge-only — append/update content, do not rewrite."
        )


def list_raw(vault: Path) -> list[Path]:
    raw = vault / "raw"
    if not raw.exists():
        return []
    out: list[Path] = []
    for p in raw.iterdir():
        if p.is_dir():
            continue
        if p.is_symlink():
            # Reject symlinks — they may point outside the vault.
            continue
        if p.name.startswith(".") or p.name == ".gitkeep":
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="List pending raw files for ingest.")
    parser.add_argument("--vault", default=str(VAULT_DEFAULT))
    args = parser.parse_args()
    pending = list_raw(Path(args.vault))
    if not pending:
        print("No pending files in raw/. Nothing to ingest.")
        return 0
    print(f"{len(pending)} files pending in raw/:")
    for p in pending:
        print(f"  - {p.name}")
    print("\nTo ingest, run `/ingest` in Claude Code (vault working dir).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
