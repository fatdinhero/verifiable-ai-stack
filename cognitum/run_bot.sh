#!/usr/bin/env bash
# run_bot.sh — Startet den COGNITUM Telegram Bot im Hintergrund.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"

PID_FILE="$SCRIPT_DIR/logs/telegram_bot.pid"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Telegram Bot laeuft bereits (PID: $PID)."
        exit 0
    fi
fi

nohup "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/telegram_bot.py" \
    >> "$SCRIPT_DIR/logs/telegram_bot.log" 2>&1 &

echo $! > "$PID_FILE"
echo "Telegram Bot gestartet. PID: $(cat "$PID_FILE")"
echo "Logs: tail -f $SCRIPT_DIR/logs/telegram_bot.log"
