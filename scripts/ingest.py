"""CLI wrapper for ingest skill. Lists raw/ files; actual ingest happens via Claude Code skill."""
from __future__ import annotations

import argparse
from pathlib import Path

VAULT_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")


def list_raw(vault: Path) -> list[Path]:
    raw = vault / "raw"
    if not raw.exists():
        return []
    out: list[Path] = []
    for p in raw.iterdir():
        if p.is_dir():
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
