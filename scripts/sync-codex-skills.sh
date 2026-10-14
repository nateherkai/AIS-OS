#!/usr/bin/env bash
# Sync canonical Claude skills (.claude/skills) into the Codex skill mirror (.agents/skills).
#
# Run this AFTER creating or editing any skill under .claude/skills/ so Codex sees the
# same content. .claude/skills is canonical. Codex reads .agents/skills, so the two must
# stay in sync. Pass one or more
# skill names to sync only those skills; omit arguments to sync everything.
#
# What it does: copies every canonical skill forward (overwrite) and applies the Codex
# path transform (.claude/skills -> .agents/skills) to markdown files only. Claude
# agent references stay under .claude/agents and scripts/binary assets copy verbatim.
#
# House rule: this script never deletes. If you RETIRE a skill (remove it from
# .claude/skills), it cannot exist in canonical anymore, so this script will WARN you to
# move the stale mirror copy to archives/ by hand (git mv), rather than deleting it.

set -euo pipefail
cd "$(dirname "$0")/.."

SRC=".claude/skills"
DST=".agents/skills"
mkdir -p "$DST"
count=0

if [ "$#" -gt 0 ]; then
  dirs=()
  for name in "$@"; do
    if [ ! -d "$SRC/$name" ]; then
      echo "ERROR: canonical skill not found: $SRC/$name" >&2
      exit 1
    fi
    dirs+=("$SRC/$name/")
  done
else
  dirs=("$SRC"/*/)
fi

for dir in "${dirs[@]}"; do
  name="$(basename "$dir")"
  cp -rf "$SRC/$name" "$DST/"
  while IFS= read -r -d '' f; do
    perl -pi -e 's#\.claude/skills/#.agents/skills/#g' "$f"
  done < <(find "$DST/$name" -name '*.md' -type f -print0)
  count=$((count + 1))
done
echo "Synced $count skills: $SRC -> $DST (transform: .claude/skills -> .agents/skills on *.md)."

# Warn about orphans: skills in the mirror with no canonical source.
if [ "$#" -eq 0 ]; then
  orphans=0
  for dir in "$DST"/*/; do
    name="$(basename "$dir")"
    if [ ! -d "$SRC/$name" ]; then
      echo "WARNING: $DST/$name has no canonical source. If the skill was retired, move it to archives/ by hand."
      orphans=$((orphans + 1))
    fi
  done
  [ "$orphans" -eq 0 ] && echo "No orphans. Mirror matches canonical."
fi
