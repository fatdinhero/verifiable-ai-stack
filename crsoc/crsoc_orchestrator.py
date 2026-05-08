#!/usr/bin/env python3
"""
crsoc/crsoc_orchestrator.py
CRSOC Vollzyklus-Runner — alle 100 Cases durch autonomous_loop getriggert

Aufruf:
    .venv/bin/python3 crsoc/crsoc_orchestrator.py --trigger batch_100
    .venv/bin/python3 crsoc/crsoc_orchestrator.py --trigger test_100
"""
from __future__ import annotations
import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# .env laden falls vorhanden (MIMO_API_KEY etc.)
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    import os as _os
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _os.environ.setdefault(_k.strip(), _v.strip())


def run(trigger: str) -> dict:
    """Fuehrt CRSOC Vollzyklus aus. Gibt Ergebnis-Dict zurueck."""
    from crsoc.crsoc import CRSOCEngine
    from crsoc.report_generator import ReportGenerator

    engine   = CRSOCEngine()
    reporter = ReportGenerator()

    # ── 8-Phasen Zyklus ──────────────────────────────────────────────────────
    result = engine.run_full_cycle(trigger)

    # ── Report speichern ─────────────────────────────────────────────────────
    report_path = reporter.save(result)
    result["report_path"] = report_path
    print(f"[CRSOC] Report gespeichert: {report_path}")

    # ── Telegram ─────────────────────────────────────────────────────────────
    sent = reporter.notify_telegram(result, report_path)
    result["telegram_sent"] = sent
    if sent:
        print("[CRSOC] Telegram-Notification gesendet")
    else:
        print("[CRSOC] Telegram-Notification fehlgeschlagen (nicht kritisch)")

    return result


def print_summary(result: dict) -> None:
    """Gibt kompakte Zusammenfassung aller 8 Phasen aus."""
    phases = result.get("phases", {})
    print("\n" + "="*60)
    print(f"  CRSOC ZYKLUS ZUSAMMENFASSUNG")
    print(f"  Trigger:  {result.get('trigger')}")
    print(f"  Zeitpunkt: {result.get('timestamp')}")
    print("="*60)

    p0 = phases.get("0_intake", {})
    print(f"\n  Phase 0 — Intake:")
    print(f"    Verarbeitete Cases:  {p0.get('processed_count', '?')}")
    print(f"    Gesamt Avg Score:    {p0.get('avg_score', '?')}")
    print(f"    Letzte 50 Avg:       {p0.get('recent_avg', '?')}")

    p1 = phases.get("1_situation", {})
    print(f"\n  Phase 1 — Situation Analysis:")
    print(f"    {p1.get('summary', '—')[:120]}")
    for imp in p1.get("improvements", [])[:2]:
        print(f"    • {imp}")

    p2 = phases.get("2_morphological", {})
    matrix = p2.get("matrix", {})
    print(f"\n  Phase 2 — Morphological Mapper ({len(matrix)} Dimensionen):")
    for dim, opts in list(matrix.items())[:3]:
        print(f"    {dim}: {' | '.join(str(o) for o in opts[:3])}")

    p3 = phases.get("3_ideas", {})
    ideas = p3.get("ideas", [])
    print(f"\n  Phase 3 — Idealisierung ({len(ideas)} Ideen via TRIZ/IFR):")
    for idea in ideas[:3]:
        print(f"    [{idea.get('name', '?')}] Impact={idea.get('impact_score', 0):.2f} "
              f"Novelty={idea.get('novelty_score', 0):.2f} "
              f"Complexity={idea.get('complexity', 0):.2f}")

    p4 = phases.get("4_evaluation", {})
    scored = p4.get("scored_ideas", [])
    print(f"\n  Phase 4 — Evaluation (VDI 2225, {len(scored)} Ideen):")
    for s in scored[:3]:
        print(f"    [{s.get('name', '?')}] VDI2225={s.get('vdi2225_score', 0):.3f}")

    p5 = phases.get("5_metabell", {})
    print(f"\n  Phase 5 — MetaBell Validation (Ψ > {p5.get('threshold', 1.4)}):")
    print(f"    Bestanden: {p5.get('passed', 0)} / {len(p5.get('validated_ideas', []))}")
    best = p5.get("best_idea", {})
    if best:
        print(f"    Beste Idee: {best.get('name', '?')} — Ψ={best.get('operator_psi', best.get('psi_score', 0)):.3f}")
    for v in p5.get("validated_ideas", [])[:3]:
        status = "PASS" if v.get("passed") or v.get("operator_psi", 0) > 1.4 else "FAIL"
        print(f"    [{status}] {v.get('name', '?')} Ψ={v.get('operator_psi', 0):.3f}")

    p6 = phases.get("6_masterplan", {})
    print(f"\n  Phase 6 — Masterplan Update + ADR:")
    print(f"    ADR:     {p6.get('adr_path', 'n/a')}")
    print(f"    Ideen:   {p6.get('ideas_saved', 0)} gespeichert")
    print(f"    Masterplan aktualisiert: {p6.get('masterplan_updated', False)}")

    p7 = phases.get("7_temporal", {})
    print(f"\n  Phase 7 — Temporal Feedback (Brier Score):")
    print(f"    Brier Score:  {p7.get('brier_score', 'n/a')}")
    print(f"    Qualitaet:    {p7.get('brier_quality', 'n/a')}")
    print(f"    Historische Eintraege: {p7.get('history_entries', 0)}")

    print("\n" + "="*60)
    print(f"  Beste Idee gesamt: {result.get('best_idea', '—')}")
    print(f"  Ψ-Score:           {result.get('best_score', 0):.3f}")
    print(f"  ADR:               {result.get('adr_path', 'n/a')}")
    print(f"  Report:            {result.get('report_path', 'n/a')}")
    print(f"  Telegram:          {'gesendet' if result.get('telegram_sent') else 'nicht gesendet'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CRSOC Vollzyklus-Orchestrator")
    parser.add_argument("--trigger", default="manual", metavar="NAME",
                        help="Trigger-Name, z.B. batch_100 oder test_100")
    args = parser.parse_args()

    try:
        result = run(args.trigger)
        print_summary(result)
        sys.exit(0)
    except Exception:
        print("[CRSOC] FEHLER:")
        traceback.print_exc()
        sys.exit(1)
