#!/usr/bin/env python3
"""
scripts/evaluate_adrs.py
Evaluiert alle ADRs in docs/adr/ und erstellt Evaluation-Report.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance.evaluator import SPALTENEvaluator


def main():
    repo_root = Path(__file__).resolve().parents[1]
    adr_dir = repo_root / "docs" / "adr"

    if not adr_dir.exists():
        print(f"ADR-Verzeichnis nicht gefunden: {adr_dir}")
        sys.exit(1)

    evaluator = SPALTENEvaluator()
    print(f"\n{'='*60}")
    print(f"ADR Evaluation Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Verzeichnis: {adr_dir}")
    print(f"{'='*60}\n")

    summary = evaluator.evaluate_all_adrs(adr_dir)

    if summary["count"] == 0:
        print("Keine ADR-Dateien gefunden.")
        sys.exit(0)

    # Terminal-Tabelle
    header = f"{'Datei':<55} {'Score':>6} {'VDI':>5} {'SPALT':>6} {'Less':>5} {'Entsch':>7}"
    print(header)
    print("-" * 82)
    for d in summary["details"]:
        vdi   = "✅" if d.get("has_vdi2225_score") else "❌"
        spalt = "✅" if d.get("has_spalten_ref") else "❌"
        less  = "✅" if d.get("has_lessons") else "❌"
        entsch = "✅" if d.get("has_decision") else "❌"
        print(f"{d['file']:<55} {d['quality_score']:>5.2f}  {vdi:>4}  {spalt:>5}  {less:>4}  {entsch:>6}")

    print("-" * 82)
    print(f"\n{'Gesamt ADRs:':<30} {summary['count']}")
    print(f"{'Durchschnitt Quality-Score:':<30} {summary['avg_quality']:.2f}")
    print(f"{'Bestes ADR:':<30} {summary['best']} ({summary['best_score']:.2f})")
    print(f"{'Schlechtestes ADR:':<30} {summary['worst']} ({summary['worst_score']:.2f})")

    # JSON-Report speichern
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = repo_root / f"evaluation_report_{ts}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Report gespeichert: {report_path.name}\n")


if __name__ == "__main__":
    main()
