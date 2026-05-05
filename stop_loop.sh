#!/usr/bin/env bash
# stop_loop.sh — Beendet den laufenden Autonomous Loop sauber via SIGTERM.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/autonomous_loop.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "Kein laufender Loop gefunden (keine PID-Datei)."
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "Prozess $PID laeuft nicht mehr. Raeume PID-Datei auf."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Sende SIGTERM an PID $PID …"
kill -TERM "$PID"

# Warten bis Prozess beendet (max 15s)
for i in $(seq 1 15); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Loop (PID $PID) erfolgreich beendet."
        exit 0
    fi
    sleep 1
done

echo "Prozess reagiert nicht — sende SIGKILL."
kill -KILL "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Loop (PID $PID) beendet (SIGKILL)."
