#!/usr/bin/env bash
# run_loop.sh — Startet den COGNITUM Autonomous Loop im Hintergrund.
# Verwendung: ./run_loop.sh [batch_size] [sleep_s] [min_score] [max_total]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/autonomous_loop.pid"
LOG_FILE="$SCRIPT_DIR/logs/autonomous_loop.log"
PYTHON="${SCRIPT_DIR}/.venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="$(command -v python3)"
fi

mkdir -p "$SCRIPT_DIR/logs"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Loop laeuft bereits (PID $PID). Nutze stop_loop.sh zum Beenden."
        exit 1
    else
        echo "Veraltete PID-Datei gefunden — wird entfernt."
        rm -f "$PID_FILE"
    fi
fi

BATCH_SIZE="${1:-3}"
SLEEP_S="${2:-60}"
MIN_SCORE="${3:-0.75}"
MAX_TOTAL="${4:-500}"

echo "Starte COGNITUM Autonomous Loop ..."
echo "  batch-size=$BATCH_SIZE  sleep=${SLEEP_S}s  min-score=$MIN_SCORE  max-total=$MAX_TOTAL"
echo "  Log: $LOG_FILE"

nohup "$PYTHON" "$SCRIPT_DIR/autonomous_loop.py" \
    --batch-size "$BATCH_SIZE" \
    --sleep      "$SLEEP_S" \
    --min-score  "$MIN_SCORE" \
    --max-total  "$MAX_TOTAL" \
    > /dev/null 2>&1 &

# Kurz warten damit PID-Datei geschrieben wird
sleep 1
if [[ -f "$PID_FILE" ]]; then
    echo "Loop gestartet. PID=$(cat "$PID_FILE") | Stopp: ./stop_loop.sh"
else
    echo "Warnung: PID-Datei noch nicht geschrieben — pruefe $LOG_FILE"
fi
