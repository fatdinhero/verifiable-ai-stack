#!/usr/bin/env python3
"""
scripts/dataset_exporter.py
Exportiert synthetische ADR-Cases in Fine-Tuning-Formate (SFT, DPO, Metadata).
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

INPUT_DIR  = REPO_ROOT / "data" / "synthetic_adrs"
OUTPUT_DIR = REPO_ROOT / "data" / "training"

SYSTEM_PROMPT = (
    "Du bist ein systematischer Konstruktionsingenieur nach VDI 2221. "
    "Analysiere technische Probleme mit der SPALTEN-Methode und VDI 2225 Bewertung. "
    "Antworte immer auf Deutsch. Sei praezise und strukturiert."
)

PHASE_LABELS = {
    "S": "Situationsanalyse",
    "P": "Problemeingrenzung",
    "A": "Alternativen (Morphologischer Kasten)",
    "L": "Loesungsauswahl (VDI 2225)",
    "T": "Tragweitenanalyse (FMEA)",
    "E": "Entscheidung",
    "N": "Lessons Learned",
}


def _load_cases() -> List[dict]:
    """Laedt alle JSON-Cases aus data/synthetic_adrs/."""
    cases = []
    for f in sorted(INPUT_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cases.append(data)
        except Exception as e:
            print(f"  Warnung: {f.name} konnte nicht geladen werden: {e}")
    return cases


def _build_assistant_content(case: dict) -> str:
    """Baut strukturierten SPALTEN-Analyse-Text aus allen Phasen."""
    lines = []
    for step in case.get("steps", []):
        phase_name = step.get("phase", "")
        # Phase-Kuerzel aus dem vollen Namen ableiten
        short = next(
            (k for k, v in PHASE_LABELS.items() if v.lower() in phase_name.lower()),
            phase_name[:1].upper(),
        )
        label = PHASE_LABELS.get(short, phase_name.title())
        lines.append(f"## {label}")
        lines.append(step.get("summary", "").strip())

        # VDI 2225 Score inline
        vdi = step.get("artifacts", {}).get("vdi2225")
        if vdi:
            lines.append(
                f"**VDI 2225:** Bestes={vdi['best']} "
                f"Score={vdi['best_score']:.2f} "
                f"Gate={'PASS' if vdi['gate_passed'] else 'FAIL'}"
            )
        lines.append("")

    if case.get("selected_solution"):
        lines.append(f"**Gewaelte Loesung:** {case['selected_solution']}")

    return "\n".join(lines).strip()


def _get_overall_score(case: dict) -> float:
    """Holt overall_score aus eingebettetem evaluation-Feld oder berechnet Fallback."""
    ev = case.get("evaluation")
    if ev and "overall_score" in ev:
        return float(ev["overall_score"])

    # Fallback: avg_confidence
    steps = case.get("steps", [])
    if not steps:
        return 0.0
    return sum(s.get("confidence", 0.5) for s in steps) / len(steps)


def _generate_rejected(problem: str, domain: str) -> str:
    """Erzeugt eine vereinfachte, nicht-methodische Antwort als DPO-rejected."""
    try:
        from spalten_agent import call_llm
        prompt = (
            f"Problem: {problem} (Domain: {domain})\n\n"
            "Gib eine kurze, allgemeine Antwort ohne strukturierte Methodik, "
            "ohne VDI-Normen und ohne Phaseneinteilung. Maximal 3 Saetze."
        )
        return call_llm(
            prompt,
            system_prompt="Du bist ein generischer Assistent ohne Fachkenntnisse.",
            temperature=0.8,
        )
    except Exception:
        return f"Fuer das Problem '{problem}' gibt es verschiedene Ansaetze. Eine einfache Loesung waere, den einfachsten Weg zu waehlen."


def export_sft(cases: List[dict], output_dir: Path) -> int:
    """Exportiert SFT-Dataset (alle Cases)."""
    out_path = output_dir / "sft_dataset.jsonl"
    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for case in cases:
            problem = case.get("problem", "")
            domain  = case.get("domain", "general")
            assistant_content = _build_assistant_content(case)
            if not assistant_content.strip():
                continue
            entry = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": f"Problem: {problem}\nDomain: {domain}"},
                    {"role": "assistant", "content": assistant_content},
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1
    print(f"  SFT: {count} Eintraege → {out_path.name}")
    return count


def export_dpo(cases: List[dict], output_dir: Path) -> int:
    """Exportiert DPO-Dataset (chosen >= 0.8, rejected via LLM)."""
    out_path = output_dir / "dpo_dataset.jsonl"
    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for case in cases:
            score = _get_overall_score(case)
            if score < 0.8:
                continue
            problem = case.get("problem", "")
            domain  = case.get("domain", "general")

            chosen   = _build_assistant_content(case)
            rejected = _generate_rejected(problem, domain)

            if not chosen.strip() or not rejected.strip():
                continue

            entry = {
                "prompt":   f"Analysiere dieses Problem: {problem} (Domain: {domain})",
                "chosen":   chosen,
                "rejected": rejected,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            count += 1
    print(f"  DPO: {count} Paare → {out_path.name}")
    return count


def export_metadata(cases: List[dict], sft_count: int, dpo_count: int,
                    output_dir: Path) -> None:
    """Exportiert Dataset-Metadaten."""
    out_path = output_dir / "dataset_metadata.json"
    scores = [_get_overall_score(c) for c in cases]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    domain_counts: Dict[str, int] = defaultdict(int)
    for c in cases:
        domain_counts[c.get("domain", "general")] += 1

    metadata = {
        "created_at":        datetime.utcnow().isoformat() + "Z",
        "total_cases":       len(cases),
        "sft_count":         sft_count,
        "dpo_pairs":         dpo_count,
        "avg_quality_score": round(avg_score, 3),
        "domains":           dict(domain_counts),
    }
    out_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Metadata: {out_path.name}")


def main() -> None:  # type: ignore[return]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Dataset Exporter — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"Input:  {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    cases = _load_cases()
    if not cases:
        print("Keine Cases gefunden. Zuerst adr_generator.py ausfuehren.")
        sys.exit(1)

    print(f"Geladene Cases: {len(cases)}\n")
    scores = [_get_overall_score(c) for c in cases]
    for c, s in zip(cases, scores):
        print(f"  {c.get('case_id','?')[:12]} | score={s:.2f} | {c.get('problem','')[:55]}")

    print()
    sft_count = export_sft(cases, OUTPUT_DIR)
    dpo_count = export_dpo(cases, OUTPUT_DIR)
    export_metadata(cases, sft_count, dpo_count, OUTPUT_DIR)

    print(f"\n{'='*60}")
    print(f"Export abgeschlossen.")
    print(f"  SFT: {sft_count} | DPO: {dpo_count} | Cases: {len(cases)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
