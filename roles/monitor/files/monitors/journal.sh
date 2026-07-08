#!/usr/bin/env bash
# Monitor: Check systemd journal for errors since last run.
# Writes one file to TEMP_DIR if errors are found.
#
# Environment variables (with defaults):
#   CURSOR_FILE  - path to persist journal cursor (default: /var/lib/monitor/cursor)
#   LOG_FILE     - path to log file (default: empty, no logging)
#   EXCLUDE_PATTERNS - pipe-separated extended regex patterns to filter out (default: empty)

set -euo pipefail

TEMP_DIR="${1:?Usage: $0 <temp_dir>}"
CURSOR_FILE="${CURSOR_FILE:-/var/lib/monitor/cursor}"
LOG_FILE="${LOG_FILE:-}"
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-}"

log() {
  if [[ -n "$LOG_FILE" ]]; then
    echo "$(date '+%F %T.%3N') $1" >> "$LOG_FILE"
  fi
}

mkdir -p "$(dirname "$CURSOR_FILE")"

log "INFO: [journal] Checking journal for new errors."

if [[ -f "$CURSOR_FILE" ]]; then
  OUTPUT=$(journalctl -p err --after-cursor "$(cat "$CURSOR_FILE")" --show-cursor --no-pager 2>/dev/null)
else
  log "INFO: [journal] No cursor file found. Processing all errors since boot."
  OUTPUT=$(journalctl -p err --show-cursor --no-pager 2>/dev/null)
fi

NEW_CURSOR=$(echo "$OUTPUT" | grep "^-- cursor:" | tail -n1 | sed 's/^-- cursor: //')
if [[ -n "$NEW_CURSOR" ]]; then
  echo "$NEW_CURSOR" > "$CURSOR_FILE"
fi

ERRORS=$(echo "$OUTPUT" | grep -v "^-- cursor:")

if [[ -n "$EXCLUDE_PATTERNS" ]]; then
  ERRORS=$(echo "$ERRORS" | grep -vE "$EXCLUDE_PATTERNS" || true)
fi

# Trim empty lines
ERRORS=$(echo "$ERRORS" | sed '/^$/d')

if [[ -n "$ERRORS" ]]; then
  log "INFO: [journal] Errors found."
  echo "$ERRORS" > "$TEMP_DIR/Journal_errors"
else
  log "INFO: [journal] No errors found."
fi
