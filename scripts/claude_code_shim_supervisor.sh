#!/bin/bash
# Supervisor loop for claude_code_shim — restarts on crash
# Usage: nohup bash claude_code_shim_supervisor.sh > /tmp/claude_shim_supervisor.log 2>&1 &
set -u

LOG=/tmp/claude_shim.log
PIDFILE=/tmp/claude_shim.pid
echo $$ > "$PIDFILE"

while true; do
  echo "[$(date -Iseconds)] starting claude_code_shim.py" >> "$LOG"
  python3 /home/bowen/.openclaw/workspace/scripts/claude_code_shim.py --host 127.0.0.1 --port 8090 >> "$LOG" 2>&1
  echo "[$(date -Iseconds)] exited code $?. restart in 5s" >> "$LOG"
  sleep 5
done
