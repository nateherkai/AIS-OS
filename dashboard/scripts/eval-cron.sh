#!/usr/bin/env bash
set -euo pipefail

# Nightly eval harness — invoked by launchd at 02:30 local
cd "/Volumes/Samsung PSSD T7/gravity-claw"

# Load .env so ANTHROPIC_API_KEY is set
if [ -f .env ]; then set -a; . .env; set +a; fi

mkdir -p "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs"

LOG_FILE="/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs/cron.log"
echo "=== $(date) ===" >> "$LOG_FILE"

npx tsx src/scripts/eval-run.ts >> "$LOG_FILE" 2>&1
