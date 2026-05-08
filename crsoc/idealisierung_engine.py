#!/usr/bin/env python3
"""
crsoc/idealisierung_engine.py
Phase 3: Idealisierung — 8 neue Ideen via TRIZ/IFR aus morphologischer Matrix
"""
from __future__ import annotations
import json
import random
from typing import Any, Dict, List
from crsoc.crsoc import _llm


class IdealisierungEngine:
    def generate(self, morph_result: Dict[str, Any], n: int = 8) -> Dict[str, Any]:
        matrix = morph_result.get("matrix", {})
        if not matrix:
            return {"ideas": [], "method": "triz_ifr"}

        # Kombiniere zufaellig Auspraegungen aus verschiedenen Dimensionen
        dims    = list(matrix.keys())
        combos  = []
        for _ in range(n):
            selected = {d: random.choice(matrix[d]) for d in random.sample(dims, min(3, len(dims)))}
            combos.append(selected)

        prompt = (
            "Wende das TRIZ-Idealisierungsprinzip (IFR) auf diese Kombinationen an.\n"
            "Ziel: Ein Privacy-First AI-Engineering-OS (DaySensOS / COGNITUM).\n\n"
            "Kombinationen:\n" + json.dumps(combos, ensure_ascii=False) + "\n\n"
            f"Generiere {n} konkrete, umsetzbare Ideen. Jede Idee hat:\n"
            "- name: kurzer Titel (max 6 Woerter)\n"
            "- description: 1 Satz was es macht\n"
            "- impact_score: float 0-1 (erwarteter Nutzen)\n"
            "- novelty_score: float 0-1 (Innovationsgrad)\n"
            "- complexity: float 0-2 (Umsetzungsaufwand, 0=trivial, 2=sehr komplex)\n\n"
            "Antworte als JSON: {\"ideas\": [{...}, ...]}"
        )
        raw = _llm(prompt, max_tokens=1000)
        try:
            parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
            ideas = parsed.get("ideas", [])
        except Exception:
            ideas = []

        # Fallback: minimale Ideen aus Kombinationen
        if not ideas:
            for i, combo in enumerate(combos[:n]):
                dims_str = ", ".join(f"{k}: {v}" for k, v in combo.items())
                ideas.append({
                    "name":          f"Idee-{i+1}",
                    "description":   f"Optimierung via {dims_str}",
                    "impact_score":  round(random.uniform(0.4, 0.9), 2),
                    "novelty_score": round(random.uniform(0.3, 0.8), 2),
                    "complexity":    round(random.uniform(0.3, 1.5), 2),
                })

        return {"ideas": ideas[:n], "method": "triz_ifr", "combos_used": combos}
