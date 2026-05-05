#!/usr/bin/env bash
# stop_bot.sh — Beendet den laufenden Telegram Bot sauber via SIGTERM.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/telegram_bot.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "Kein laufender Bot gefunden (keine PID-Datei)."
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "Prozess $PID laeuft nicht mehr. Raeume PID-Datei auf."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Sende SIGTERM an PID $PID ..."
kill -TERM "$PID"

for i in $(seq 1 15); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Telegram Bot (PID $PID) erfolgreich beendet."
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

echo "Prozess reagiert nicht — sende SIGKILL."
kill -KILL "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Telegram Bot (PID $PID) beendet (SIGKILL)."
