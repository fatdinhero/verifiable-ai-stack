#!/usr/bin/env bash
# status_loop.sh — Zeigt Status, .loop_state.json, Log-Tail und Rate/h
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/autonomous_loop.pid"
LOG_FILE="$SCRIPT_DIR/logs/autonomous_loop.log"
STATE_FILE="$SCRIPT_DIR/.loop_state.json"

echo "═══════════════════════════════════════════════════════"
echo " COGNITUM Autonomous Loop — Status"
echo "═══════════════════════════════════════════════════════"

# Prozess-Status
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo " Status   : LAUFEND (PID=$PID)"
        UPTIME=$(ps -p "$PID" -o etime= 2>/dev/null | tr -d ' ' || echo "?")
        echo " Laufzeit : $UPTIME"
    else
        echo " Status   : GESTOPPT (veraltete PID=$PID)"
    fi
else
    echo " Status   : NICHT GESTARTET"
fi

# .loop_state.json
echo ""
echo "─── .loop_state.json ──────────────────────────────────"
if [[ -f "$STATE_FILE" ]]; then
    python3 - "$STATE_FILE" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
processed  = d.get("processed_count", 0)
skipped    = d.get("skipped_count",   0)
avg_score  = d.get("avg_score",       0.0)
last_run   = d.get("last_run",        "—")
runtime_s  = d.get("total_runtime_s", 0)
batches    = d.get("batch_count",     0)
sources    = d.get("signal_sources",  {})
rate_h     = round(3600 * processed / max(runtime_s, 1), 1)
print(f" Verarbeitet  : {processed}")
print(f" Uebersprungen: {skipped}")
print(f" Batches      : {batches}")
print(f" Ø Score      : {avg_score:.3f}")
print(f" Rate         : ~{rate_h} Cases/h")
print(f" Letzter Run  : {last_run}")
print(f" Signal-Src   : {json.dumps(sources)}")
print()
print("─── Vollstaendiges JSON ───────────────────────────────")
print(json.dumps(d, indent=2, ensure_ascii=False))
PYEOF
else
    echo " Keine State-Datei (.loop_state.json) — Loop noch nicht gestartet."
fi

# Log-Tail
echo ""
echo "─── Letzte 20 Log-Eintraege ───────────────────────────"
if [[ -f "$LOG_FILE" ]]; then
    tail -20 "$LOG_FILE"
else
    echo " (kein Log vorhanden)"
fi
echo "═══════════════════════════════════════════════════════"
