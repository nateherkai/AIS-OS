#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# super-aios.sh — Bryan's Unified AI Operating System Launch Script
#
# Starts:
#   1. AIS-OS Dashboard (FastAPI on port 8080)
#   2. Hermes Agent (CLI or gateway, configurable)
#
# Usage:
#   ./super-aios.sh          — dashboard + Hermes CLI
#   ./super-aios.sh gateway  — dashboard + Hermes Telegram gateway
#   ./super-aios.sh dash     — dashboard only (no Hermes)
#   ./super-aios.sh kill     — stop all running instances
# ─────────────────────────────────────────────────────────────────────────────

set -o pipefail

AIOS_ROOT="/Volumes/Samsung PSSD T7/AIS-OS"
HERMES_ROOT="/Volumes/Samsung PSSD T7/hermes-claw"
PID_FILE="$AIOS_ROOT/.super-aios.pids"
LOG_DIR="$HOME/Library/Logs/super-aios"
DASHBOARD_PORT=8080
MODE="${1:-cli}"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
MAROON='\033[0;31m'; BOLD='\033[1m'; RESET='\033[0m'

banner() { echo -e "${BOLD}${MAROON}╔══════════════════════════════════════════╗${RESET}"; \
           echo -e "${BOLD}${MAROON}║       BRYAN'S SUPER AI/AGENT OS          ║${RESET}"; \
           echo -e "${BOLD}${MAROON}╚══════════════════════════════════════════╝${RESET}"; }
ok()     { echo -e "${GREEN}✓${RESET} $1"; }
info()   { echo -e "${BLUE}→${RESET} $1"; }
warn()   { echo -e "${YELLOW}⚠${RESET} $1"; }
die()    { echo -e "${RED}✗${RESET} $1"; exit 1; }

# ── Kill mode ─────────────────────────────────────────────────────────────────
if [ "$MODE" = "kill" ]; then
  echo "Stopping Super AIOS…"
  if [ -f "$PID_FILE" ]; then
    while IFS= read -r pid; do
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" && echo "  killed PID $pid"
      fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
  fi
  # Belt-and-suspenders: also kill by port
  lsof -ti tcp:$DASHBOARD_PORT | xargs kill -9 2>/dev/null || true
  ok "All Super AIOS processes stopped."
  exit 0
fi

# ── Setup ─────────────────────────────────────────────────────────────────────
banner
mkdir -p "$LOG_DIR"
> "$PID_FILE"

# ── Pre-flight checks ─────────────────────────────────────────────────────────
info "Running pre-flight checks…"

[ -d "$AIOS_ROOT" ]   || die "AIS-OS root not found: $AIOS_ROOT"
[ -d "$HERMES_ROOT" ] || die "Hermes root not found: $HERMES_ROOT"
[ -f "$AIOS_ROOT/dashboard/server.py" ] || die "dashboard/server.py not found"

command -v python3 >/dev/null || die "python3 not found"
command -v uv      >/dev/null || warn "uv not found — using pip/python3 directly"

# Check if dashboard port is already in use
if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  warn "Port $DASHBOARD_PORT already in use — dashboard may already be running"
  warn "Run './super-aios.sh kill' first if you want a fresh start"
fi

ok "Pre-flight complete"

# ── Load environment ──────────────────────────────────────────────────────────
if [ -f "$AIOS_ROOT/.env" ]; then
  # Safe loader — skips lines with spaces in key name (e.g. "Supabase URL=...")
  # Only exports valid shell variable names: letters, digits, underscores, no spaces
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip blank lines and comments
    [[ -z "${line// }" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    # Extract key (everything before first =)
    key="${line%%=*}"
    # Skip if key contains spaces or is not a valid shell identifier
    [[ "$key" =~ [[:space:]] ]] && continue
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    # Export safely
    export "$line" 2>/dev/null || true
  done < "$AIOS_ROOT/.env"
  ok "Loaded AIS-OS .env (safe mode)"
fi

# Re-pin critical vars in case .env overwrote them
DASHBOARD_PORT=${DASHBOARD_PORT:-8080}
AIOS_ROOT="/Volumes/Samsung PSSD T7/AIS-OS"
HERMES_ROOT="/Volumes/Samsung PSSD T7/hermes-claw"

# Set vault path for Hermes memory router
export HERMES_VAULT_PATH="$AIOS_ROOT/Bryan-Aaron-Master/wiki"
export HERMES_SOUL_PATH="$HERMES_ROOT/hermes/memory/soul.md"
ok "Memory paths configured"

# ── Start AIS-OS Dashboard ────────────────────────────────────────────────────
info "Starting AIS-OS Dashboard on port $DASHBOARD_PORT…"
cd "$AIOS_ROOT/dashboard"
python3 server.py \
  >> "$LOG_DIR/dashboard.log" \
  2>> "$LOG_DIR/dashboard.err" &
DASH_PID=$!
echo "$DASH_PID" >> "$PID_FILE"

# Wait for dashboard to be ready
for i in $(seq 1 15); do
  if curl -sf "http://localhost:$DASHBOARD_PORT/" >/dev/null 2>&1; then
    ok "Dashboard ready — http://localhost:$DASHBOARD_PORT"
    break
  fi
  sleep 0.5
done
# Non-fatal if it takes longer — just open the browser and it'll catch up

# ── Start Hermes ──────────────────────────────────────────────────────────────
cd "$HERMES_ROOT"

if [ "$MODE" = "dash" ]; then
  warn "Dashboard-only mode — Hermes not started"
elif [ "$MODE" = "gateway" ]; then
  info "Starting Hermes gateway (Telegram/Discord)…"
  python3 -m hermes gateway \
    >> "$LOG_DIR/hermes-gateway.log" \
    2>> "$LOG_DIR/hermes-gateway.err" &
  HERMES_PID=$!
  echo "$HERMES_PID" >> "$PID_FILE"
  ok "Hermes gateway started (PID $HERMES_PID)"
  info "Tail gateway logs: tail -f $LOG_DIR/hermes-gateway.log"
else
  info "Hermes CLI is available — run 'hermes' or '@Bryan' to activate persona"
  info "For gateway mode: ./super-aios.sh gateway"
fi

# ── Open Browser ──────────────────────────────────────────────────────────────
sleep 0.5
open "http://localhost:$DASHBOARD_PORT/hermes-panel.html" 2>/dev/null || true
ok "Opened Hermes control surface in browser"

# ── Status summary ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Super AIOS running:${RESET}"
echo "  Dashboard:  http://localhost:$DASHBOARD_PORT"
echo "  Hermes:     http://localhost:$DASHBOARD_PORT/hermes-panel.html"
echo "  Logs:       $LOG_DIR/"
echo "  PIDs:       $PID_FILE"
echo ""
echo -e "${MAROON}Stop everything:${RESET} ./super-aios.sh kill"
echo -e "${BLUE}Hermes CLI:${RESET}       cd $HERMES_ROOT && hermes"
echo -e "${BLUE}Bryan persona:${RESET}    @Bryan <your message>"
echo ""
