"""
corpus/builder.py — Build a quality-filtered JSONL corpus from SPALTEN engineering cases.

Reads all JSON files from data/synthetic_adrs/, scores each case, and exports
high-quality cases (final_score >= 0.7) to data/corpus_assets/cognitum_engineering_v1.jsonl.

Score formula:
    confidence_mean = average confidence of all phase steps
    completeness    = len(steps) / 7   (7 SPALTEN phases)
    has_artifacts   = 1.0 if any step contains morphologie_matrix, else 0.0
    final_score     = confidence_mean * 0.5 + completeness * 0.3 + has_artifacts * 0.2

Usage:
    python3 corpus/builder.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).parent.parent
INPUT_DIR = ROOT / "data" / "synthetic_adrs"
OUTPUT_DIR = ROOT / "data" / "corpus_assets"
OUTPUT_FILE = OUTPUT_DIR / "cognitum_engineering_v1.jsonl"

SCORE_THRESHOLD = 0.7
TOTAL_PHASES = 7


def _score_case(case: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Compute DQM score for one case. Returns (final_score, breakdown)."""
    steps: List[Dict[str, Any]] = case.get("steps", [])

    confidences = [s.get("confidence", 0.0) for s in steps if isinstance(s.get("confidence"), (int, float))]
    confidence_mean = sum(confidences) / len(confidences) if confidences else 0.0

    completeness = min(len(steps) / TOTAL_PHASES, 1.0)

    has_artifacts = 0.0
    for step in steps:
        artifacts = step.get("artifacts") or {}
        if "morphologie_matrix" in artifacts or "vdi2225" in artifacts:
            has_artifacts = 1.0
            break

    final_score = confidence_mean * 0.5 + completeness * 0.3 + has_artifacts * 0.2
    breakdown = {
        "confidence_mean": round(confidence_mean, 4),
        "completeness": round(completeness, 4),
        "has_artifacts": has_artifacts,
        "final_score": round(final_score, 4),
    }
    return final_score, breakdown


def _load_cases(input_dir: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Load all JSON case files. Returns list of (filename, case_dict)."""
    cases = []
    for fname in sorted(input_dir.iterdir()):
        if fname.suffix != ".json":
            continue
        try:
            with open(fname, encoding="utf-8") as fh:
                case = json.load(fh)
            cases.append((fname.name, case))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  ⚠️  Skip {fname.name}: {exc}", file=sys.stderr)
    return cases


def build_corpus(
    input_dir: Path = INPUT_DIR,
    output_file: Path = OUTPUT_FILE,
    threshold: float = SCORE_THRESHOLD,
) -> Dict[str, Any]:
    """Load cases, score them, export passing ones as JSONL. Returns stats."""
    if not input_dir.exists():
        print(f"Input dir not found: {input_dir}", file=sys.stderr)
        return {}

    output_file.parent.mkdir(parents=True, exist_ok=True)

    cases = _load_cases(input_dir)
    total = len(cases)
    passed_cases: List[Dict[str, Any]] = []
    scores: List[float] = []

    for fname, case in cases:
        final_score, breakdown = _score_case(case)
        scores.append(final_score)
        if final_score >= threshold:
            record = {
                "source_file": fname,
                "case_id": case.get("case_id", ""),
                "title": case.get("title", ""),
                "problem": case.get("problem", ""),
                "domain": case.get("domain", ""),
                "selected_solution": case.get("selected_solution", ""),
                "steps": case.get("steps", []),
                "dqm": breakdown,
            }
            passed_cases.append(record)

    with open(output_file, "w", encoding="utf-8") as fh:
        for record in passed_cases:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    mean_score = sum(scores) / len(scores) if scores else 0.0
    stats = {
        "total": total,
        "passed": len(passed_cases),
        "failed": total - len(passed_cases),
        "mean_score": round(mean_score, 4),
        "threshold": threshold,
        "output_file": str(output_file),
    }
    return stats


def main() -> None:
    print(f"📂 Reading cases from: {INPUT_DIR}")
    stats = build_corpus()
    if not stats:
        sys.exit(1)
    print(f"\n{'='*50}")
    print(f"  Total cases  : {stats['total']}")
    print(f"  Passed (≥{stats['threshold']}) : {stats['passed']}")
    print(f"  Failed       : {stats['failed']}")
    print(f"  Mean score   : {stats['mean_score']:.4f}")
    print(f"  Output       : {stats['output_file']}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
