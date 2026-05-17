#!/usr/bin/env bash
# Mirror ag-coach-app .md files into vault. Idempotent — overwrites existing mirror.
set -euo pipefail
SRC="/Volumes/Samsung PSSD T7/ag-coach-app"
DST="/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/01-AG-COACH-PRO/App-Source"
mkdir -p "$DST"

# Find + copy
cd "$SRC"
find . -name "*.md" \
  -not -path "./node_modules/*" \
  -not -path "./.next/*" \
  -not -path "./.expo/*" \
  -not -path "./.vercel/*" \
  -not -path "./dist/*" \
  -not -path "./build/*" \
  -not -path "*/worktrees/*" \
  -not -path "*/.pytest_cache/*" \
  -not -path "*/__pycache__/*" \
  -not -path "./.git/*" \
  -not -path "./.venv/*" \
  -not -path "./.tmp/*" \
  -not -path "*/coverage/*" | while IFS= read -r f; do
    rel="${f#./}"
    dst="$DST/$rel"
    mkdir -p "$(dirname "$dst")"
    cp "$f" "$dst"
  done

# Regenerate INDEX
INDEX="$DST/_INDEX.md"
{
  echo "# Ag Coach Pro — App Source Mirror"
  echo ""
  echo "> Snapshot of \`$SRC\` .md files"
  echo "> Last refreshed: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "> Total files: $(find "$DST" -name '*.md' -not -name '_INDEX.md' | wc -l | tr -d ' ')"
  echo ""
  echo "## Folder tree"
  echo ""
  echo '```'
  cd "$DST" && find . -name "*.md" -not -name "_INDEX.md" | sort | head -300
  echo '```'
} > "$INDEX"

echo "Mirrored $(find "$DST" -name '*.md' -not -name '_INDEX.md' | wc -l | tr -d ' ') files to $DST"
