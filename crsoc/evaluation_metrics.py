#!/usr/bin/env python3
"""
crsoc/evaluation_metrics.py
Phase 4: Multi-Kriterien Bewertung der Ideen (VDI 2225)
"""
from __future__ import annotations
from typing import Any, Dict, List


class EvaluationMetrics:
    WEIGHTS = {
        "impact_score":   0.40,
        "novelty_score":  0.30,
        "feasibility":    0.30,  # inverse complexity
    }

    def score(self, ideas_result: Dict[str, Any]) -> Dict[str, Any]:
        ideas = ideas_result.get("ideas", [])
        if not ideas:
            return {"scored_ideas": [], "top_score": 0.0, "top_idea": None}

        scored: List[Dict[str, Any]] = []
        for idea in ideas:
            impact     = float(idea.get("impact_score",  0.5))
            novelty    = float(idea.get("novelty_score", 0.5))
            complexity = float(idea.get("complexity",    1.0))
            feasibility = max(0.0, 1.0 - complexity / 2.0)

            vdi2225 = round(
                self.WEIGHTS["impact_score"]  * impact +
                self.WEIGHTS["novelty_score"] * novelty +
                self.WEIGHTS["feasibility"]   * feasibility,
                4,
            )
            scored.append({
                **idea,
                "feasibility":  round(feasibility, 3),
                "vdi2225_score": vdi2225,
            })

        scored.sort(key=lambda x: x["vdi2225_score"], reverse=True)
        top = scored[0] if scored else {}

        return {
            "scored_ideas": scored,
            "top_score":    top.get("vdi2225_score", 0.0),
            "top_idea":     top.get("name"),
            "count":        len(scored),
        }
