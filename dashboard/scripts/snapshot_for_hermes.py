"""Write AIOS state snapshot files into hermes-claw/hermes/state/.

Implements the push half of decisions/0001-aios-hermes-push-model.md.
Replaces dead HTTP pull bridge (Cloudflare 403 from Railway).

Usage:
  python3 -m scripts.snapshot_for_hermes [--no-commit] [--dest <path>]

Schedule via launchd / cron: daily 07:00 + on /wrapup.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/ is in sys.path when run as `python3 -m scripts.snapshot_for_hermes`
# from dashboard/, but `import bridge` collides with dashboard/bridge/ package.
# Import sibling explicitly.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import bridge as bridge_mod  # noqa: E402

DEFAULT_DEST = Path("/Volumes/Samsung PSSD T7/hermes-claw/hermes/state")
SLICES = ("pipeline", "dreams", "roi", "pillars")


def _read_tasks() -> dict:
    """Pull in-flight task list — not part of bridge.snapshot but useful for Hermes."""
    path = Path(__file__).parent.parent / "data" / "tasks.json"
    if not path.exists():
        return {"tasks": []}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"tasks": [], "error": "tasks.json invalid"}


def write_state(dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    snap = bridge_mod.snapshot(list(SLICES))
    files_written = []
    for key in SLICES:
        body = snap.get(key, {})
        path = dest / f"{key}.json"
        path.write_text(json.dumps(body, indent=2, default=str))
        files_written.append(path.name)

    tasks_path = dest / "tasks.json"
    tasks_path.write_text(json.dumps(_read_tasks(), indent=2, default=str))
    files_written.append(tasks_path.name)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aios_version": bridge_mod.VERSION,
        "files_written": files_written,
        "scopes": list(SLICES) + ["tasks"],
    }
    (dest / "snapshot.meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def commit_and_push(repo: Path, message: str) -> tuple[bool, str]:
    """Best-effort git commit + push. Returns (ok, summary)."""
    try:
        subprocess.run(["git", "-C", str(repo), "add", "hermes/state/"], check=True,
                       capture_output=True, text=True)
        diff = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet"],
                              capture_output=True, text=True)
        if diff.returncode == 0:
            return True, "no changes"
        subprocess.run(["git", "-C", str(repo), "commit", "-m", message], check=True,
                       capture_output=True, text=True)
        push = subprocess.run(["git", "-C", str(repo), "push", "origin", "main"],
                              capture_output=True, text=True)
        if push.returncode != 0:
            return False, f"push failed: {push.stderr.strip()[:200]}"
        return True, "pushed"
    except subprocess.CalledProcessError as e:
        return False, f"git error: {e.stderr.strip()[:200] if e.stderr else e}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot AIOS state into hermes-claw/hermes/state/.")
    parser.add_argument("--dest", default=str(DEFAULT_DEST),
                        help=f"Output dir (default: {DEFAULT_DEST})")
    parser.add_argument("--no-commit", action="store_true", help="Skip git commit/push.")
    args = parser.parse_args(argv)

    dest = Path(args.dest)
    if not dest.parent.parent.exists():
        print(f"hermes-claw root not mounted at {dest.parent.parent}", file=sys.stderr)
        return 2

    meta = write_state(dest)
    print(json.dumps({"wrote": meta["files_written"], "dest": str(dest)}, indent=2))

    if not args.no_commit:
        repo = dest.parent.parent  # hermes-claw root
        msg = f"state: AIOS snapshot {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ok, summary = commit_and_push(repo, msg)
        print(f"git: {summary}")
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
