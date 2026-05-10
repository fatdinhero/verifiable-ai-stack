#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/COS/cognitum"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  COGNITUM Engineering Agent v0.2 — Deploy              ║"
echo "║  VDI 2221 + VDI 2225 + SPALTEN + FMEA + DoE           ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

echo "📦 [1/5] Dependencies installieren..."
python3 -m pip install -q pydantic pyyaml pytest 2>&1 | tail -1

echo "📁 [2/5] Dateien kopieren..."
mkdir -p "$ROOT/governance"
cp "$SRC/governance/__init__.py" "$ROOT/governance/"
cp "$SRC/governance/registry.py" "$ROOT/governance/"
cp "$SRC/governance/models.py" "$ROOT/governance/"
cp "$SRC/spalten_agent.py" "$ROOT/"
mkdir -p "$ROOT/tests"
cp "$SRC/tests/test_registry.py" "$ROOT/tests/"

echo "🧪 [3/5] Tests (16 Stueck)..."
cd "$ROOT"
python3 -m pytest tests/test_registry.py -v --tb=short

echo "🔍 [4/5] Pydantic + VDI 2225..."
python3 -c "
from governance.models import EngineeringCase
from governance.registry import vdi2225_evaluate, morphologischer_kasten
c = EngineeringCase(title='Test', problem='Test')
print(f'  Pydantic OK: {c.case_id}')
m = morphologischer_kasten({'A': ['1','2'], 'B': ['x','y']})
print(f'  Morphologie OK: {len(m)} Varianten')
r = vdi2225_evaluate({'V1': {'t': 4}}, {'t': 1.0})
print(f'  VDI 2225 OK: Score={r[\"best_score\"]:.2f}')
"

echo "🔍 [5/5] Compliance-Registry..."
python3 -c "from governance.registry import get_ta_laerm, calculate_rpn, get_action_priority; print(f'  TA Laerm reines_wohn nacht: {get_ta_laerm(\"reines_wohn\", \"nacht\")} dB(A)'); print(f'  RPZ(8,5,3) = {calculate_rpn(8,5,3)}'); print(f'  AP(9,3,3) = {get_action_priority(9,3,3)}')"

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  ✅ Engineering Agent v0.2 deployt!                     ║"
echo "║                                                         ║"
echo "║  Tools: TA Laerm, GEG, BEG, FMEA RPZ+AP, NWA,         ║"
echo "║         VDI 2225 Bewertung, Morphologischer Kasten      ║"
echo "║                                                         ║"
echo "║  Erster SPALTEN-Durchlauf:                              ║"
echo "║  cd ~/COS/cognitum && python3 spalten_agent.py          ║"
echo "╚═══════════════════════════════════════════════════════╝"
