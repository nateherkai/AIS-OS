#!/bin/bash
# Install Dream Machine schedule — launchd on macOS, crontab elsewhere.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO/dashboard/scripts/dream_machine.py"
PYTHON="$(command -v python3)"

if [[ ! -x "$PYTHON" || ! -f "$SCRIPT" ]]; then
  echo "Missing python3 or dream_machine.py — aborting" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  PLIST="$HOME/Library/LaunchAgents/com.agcoachpro.aios.dream.plist"
  LOG_DIR="$HOME/Library/Logs/aios"
  mkdir -p "$LOG_DIR"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.agcoachpro.aios.dream</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$SCRIPT</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>2</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$LOG_DIR/dream.out.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/dream.err.log</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "✓ launchd agent installed: $PLIST"
  echo "  Runs daily at 02:00. Logs: $LOG_DIR/"
  echo "  Verify: launchctl list | grep agcoachpro.aios.dream"
else
  LINE="0 2 * * * cd $REPO && $PYTHON $SCRIPT >> $HOME/.aios-dream.log 2>&1"
  (crontab -l 2>/dev/null | grep -v "dream_machine.py" ; echo "$LINE") | crontab -
  echo "✓ crontab entry installed"
  crontab -l | grep dream_machine.py
fi
