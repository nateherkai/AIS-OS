#!/usr/bin/env bash
# Install / uninstall AIOS cadence launchd jobs (macOS).
# Usage:
#   scripts/install_cadence.sh install   # write plists + load them
#   scripts/install_cadence.sh uninstall # unload + delete plists
#   scripts/install_cadence.sh status    # show loaded jobs
#
# Idempotent: re-running `install` overwrites plists with current paths.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs/aios"
PY="$(command -v python3)"

mkdir -p "$LAUNCH_DIR" "$LOG_DIR"

# job_name | cron_args | command...
# cron_args: hour minute [weekday]   (weekday: 0=Sun..6=Sat; omit for daily)
JOBS=(
  "revenue|6 0|$PY|$REPO/scripts/revenue_snapshot.py"
  "trial|7 0 1|bash|-lc|cd \"$REPO\" && claude -p \"/trial-follow-up draft-only\" --output-format text"
  "eval|21 0 0|bash|-lc|cd \"$REPO\" && claude -p \"/eval\" --output-format text"
  "hot|2 30|bash|-lc|cd \"$REPO\" && claude -p \"/hot\" --output-format text"
  "lint|18 0 5|bash|-lc|cd \"$REPO\" && claude -p \"/lint\" --output-format text"
)

write_plist() {
  local name="$1"; shift
  local cron="$1"; shift
  local plist="$LAUNCH_DIR/com.agcoachpro.aios.${name}.plist"

  read -r HOUR MIN WEEKDAY <<<"$cron"

  # Build StartCalendarInterval block
  local cal="<dict><key>Hour</key><integer>${HOUR}</integer><key>Minute</key><integer>${MIN}</integer>"
  if [[ -n "${WEEKDAY:-}" ]]; then
    cal+="<key>Weekday</key><integer>${WEEKDAY}</integer>"
  fi
  cal+="</dict>"

  # Build ProgramArguments block
  local args="<array>"
  for a in "$@"; do
    # escape XML
    local esc; esc=$(printf '%s' "$a" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    args+="<string>${esc}</string>"
  done
  args+="</array>"

  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.agcoachpro.aios.${name}</string>
  <key>ProgramArguments</key>${args}
  <key>WorkingDirectory</key><string>${REPO}</string>
  <key>StartCalendarInterval</key>${cal}
  <key>StandardOutPath</key><string>${LOG_DIR}/${name}.log</string>
  <key>StandardErrorPath</key><string>${LOG_DIR}/${name}.err</string>
</dict></plist>
EOF
  echo "wrote $plist"
}

cmd_install() {
  for spec in "${JOBS[@]}"; do
    IFS='|' read -r name cron rest <<<"$spec"
    # Re-split the rest by | to get command args
    IFS='|' read -ra cmdparts <<<"$rest"
    write_plist "$name" "$cron" "${cmdparts[@]}"
    launchctl unload "$LAUNCH_DIR/com.agcoachpro.aios.${name}.plist" 2>/dev/null || true
    launchctl load "$LAUNCH_DIR/com.agcoachpro.aios.${name}.plist"
    echo "loaded com.agcoachpro.aios.${name}"
  done
  echo "done. status: scripts/install_cadence.sh status"
}

cmd_uninstall() {
  for spec in "${JOBS[@]}"; do
    IFS='|' read -r name _ _ <<<"$spec"
    local plist="$LAUNCH_DIR/com.agcoachpro.aios.${name}.plist"
    launchctl unload "$plist" 2>/dev/null || true
    rm -f "$plist"
    echo "removed com.agcoachpro.aios.${name}"
  done
}

cmd_status() {
  launchctl list | awk '/com.agcoachpro.aios/{print}'
}

case "${1:-status}" in
  install) cmd_install ;;
  uninstall) cmd_uninstall ;;
  status) cmd_status ;;
  *) echo "usage: $0 {install|uninstall|status}"; exit 2 ;;
esac
