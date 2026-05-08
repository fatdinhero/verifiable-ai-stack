#!/usr/bin/env python3
"""
crsoc/morphological_mapper.py
Phase 2: Morphologischer Kasten — 7 Dimensionen
"""
from __future__ import annotations
import json
from typing import Any, Dict
from crsoc.crsoc import _llm

DIMENSIONS = [
    "Funktionalitaet",
    "Technologie",
    "Markt",
    "Compliance",
    "Sicherheit",
    "Wirtschaftlichkeit",
    "Zukunftsfaehigkeit",
]


class MorphologicalMapper:
    def map(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        summary      = situation.get("summary", "")
        improvements = situation.get("improvements", [])

        prompt = (
            "Erstelle einen morphologischen Kasten (VDI 2221) fuer ein Privacy-First AI-Engineering-System.\n\n"
            f"Situation: {summary}\n"
            f"Verbesserungspotentiale: {'; '.join(improvements)}\n\n"
            "Dimensionen (je 3 Auspraegungen als String-Liste):\n"
            + "\n".join(f"- {d}" for d in DIMENSIONS) + "\n\n"
            "Antworte als JSON: {\"matrix\": {\"Dimension\": [\"Option1\", \"Option2\", \"Option3\"], ...}}"
        )
        raw = _llm(prompt, max_tokens=700)
        try:
            parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
            matrix = parsed.get("matrix", {})
        except Exception:
            matrix = {d: [f"{d}-Option-A", f"{d}-Option-B", f"{d}-Option-C"] for d in DIMENSIONS}

        # Fehlende Dimensionen auffuellen
        for d in DIMENSIONS:
            if d not in matrix:
                matrix[d] = [f"{d}-Fallback-A", f"{d}-Fallback-B"]

        return {
            "matrix":      matrix,
            "dimensions":  DIMENSIONS,
            "situation_ref": summary[:100],
        }
