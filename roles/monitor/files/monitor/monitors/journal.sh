#!/usr/bin/env bash
# Monitor: Check systemd journal for errors in the last POLL_INTERVAL minutes.
# Writes one file to TEMP_DIR if errors are found.
#
# Environment variables (with defaults):
#   POLL_INTERVAL    - minutes to look back (default: 15)
#   LOG_FILE         - path to log file (default: empty, no logging)
#   EXCLUDE_PATTERNS - pipe-separated extended regex patterns to filter out (default: empty)

set -euo pipefail

TEMP_DIR="${1:?Usage: $0 <temp_dir>}"
POLL_INTERVAL="${POLL_INTERVAL:-15}"
LOG_FILE="${LOG_FILE:-}"
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-}"

log() {
  local line
  line="$(date '+%Y-%m-%d %H:%M:%S.%3N') $1"
  echo "$line"
  if [[ -n "$LOG_FILE" ]]; then
    echo "$line" >> "$LOG_FILE"
  fi
}

log "INFO: [journal] Checking journal for errors in the last ${POLL_INTERVAL} minutes."

ERRORS=$(journalctl -p err --since "-${POLL_INTERVAL}min" --no-pager 2>/dev/null)

if [[ -n "$EXCLUDE_PATTERNS" ]]; then
  ERRORS=$(echo "$ERRORS" | grep -vE "$EXCLUDE_PATTERNS" || true)
fi

ERRORS=$(echo "$ERRORS" | grep -v "^--" | sed '/^$/d')

if [[ -n "$ERRORS" ]]; then
  log "INFO: [journal] Errors found."
  echo "$ERRORS" > "$TEMP_DIR/Journal_errors"
else
  log "INFO: [journal] No errors found."
fi
