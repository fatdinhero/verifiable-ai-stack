#!/usr/bin/env python3
"""
crsoc/temporal_feedback.py
Phase 7: Temporal Feedback — Brier Score fuer Vorhersagequalitaet
Verfolgt ob CRSOC-Ideen tatsaechlich Scores verbessern.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT  = Path(__file__).resolve().parents[1]
BRIER_FILE = REPO_ROOT / "reports" / "brier_history.json"


def _load_history() -> List[Dict[str, Any]]:
    if BRIER_FILE.exists():
        try:
            return json.loads(BRIER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    BRIER_FILE.parent.mkdir(parents=True, exist_ok=True)
    BRIER_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


class TemporalFeedback:
    def compute(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Berechnet Brier Score aus aktuellen Vorhersagen vs. historischen Actuals."""
        history = _load_history()
        top_score = evaluation.get("top_score", 0.0)

        # Brier Score: (predicted - actual)² gemittelt ueber Vorhersagen
        # predicted = vdi2225_score als Wahrscheinlichkeit dass Idee gut ist
        # actual = ob vorherige Top-Ideen tatsaechlich gut waren (vereinfacht: avg score > 0.75)
        if len(history) >= 2:
            pairs = [
                (entry["predicted"], entry.get("actual", entry["predicted"]))
                for entry in history[-20:]
                if "predicted" in entry
            ]
            if pairs:
                brier = round(sum((p - a) ** 2 for p, a in pairs) / len(pairs), 4)
            else:
                brier = None
        else:
            brier = None

        # Aktuelle Vorhersage speichern
        new_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "predicted": top_score,
            "actual":    None,  # wird beim naechsten Zyklus befuellt
            "cycle_ideas": evaluation.get("count", 0),
        }

        # Letzten Eintrag mit actual befuellen (vereinfacht: aktueller avg_score Loop)
        if history:
            prev = history[-1]
            if prev.get("actual") is None:
                prev["actual"] = top_score  # Proxy: bester Score dieses Zyklus

        history.append(new_entry)
        _save_history(history[-100:])  # Max 100 Eintraege

        return {
            "brier_score":     brier,
            "brier_quality":   _brier_label(brier),
            "history_entries": len(history),
            "current_prediction": top_score,
        }


def _brier_label(brier: float | None) -> str:
    if brier is None:
        return "insufficient_data"
    if brier < 0.05:
        return "excellent"
    if brier < 0.15:
        return "good"
    if brier < 0.25:
        return "moderate"
    return "poor"
