#!/usr/bin/env python3
"""
governance/evaluator.py
Deterministischer + LLM-basierter Qualitaets-Evaluator fuer SPALTEN-Durchlaeufe.
"""
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

from governance.models import EngineeringCase, SPALTENPhase

OLLAMA_URL = "http://localhost:11434/api/chat"
JUDGE_MODEL = "qwen2.5:7b"

# Gewichte fuer overall_score
_WEIGHTS = {
    "spalten_completeness": 0.25,
    "avg_confidence":       0.20,
    "vdi2225_gate_passed":  0.20,
    "adr_generated":        0.15,
    "fmea_present":         0.10,
    "lessons_norm":         0.05,  # min(lessons_count/3, 1.0)
    "rag_context_used":     0.05,
}

# ADR-Qualitaets-Checks und ihre Gewichte
_ADR_CHECKS = {
    "has_vdi2225_score": ("VDI 2225 Score", 0.30),
    "has_spalten_ref":   ("SPALTEN",        0.25),
    "has_lessons":       ("Lessons",        0.25),
    "has_decision":      ("Entscheidung",   0.20),
}

ALL_PHASES = {p.name for p in SPALTENPhase}


class SPALTENEvaluator:

    # ─── Deterministisch ──────────────────────────────────────────────────

    def evaluate_case(self, case: EngineeringCase) -> Dict[str, Any]:
        """Deterministisches Quality-Gate fuer einen SPALTEN-Durchlauf."""
        present_phases = {s.phase.name for s in case.steps}
        completeness = len(present_phases) / len(ALL_PHASES)

        node_l = next((s for s in case.steps if s.phase == SPALTENPhase.L), None)
        node_t = next((s for s in case.steps if s.phase == SPALTENPhase.T), None)
        node_e = next((s for s in case.steps if s.phase == SPALTENPhase.E), None)
        node_n = next((s for s in case.steps if s.phase == SPALTENPhase.N), None)
        node_s = next((s for s in case.steps if s.phase == SPALTENPhase.S), None)

        vdi2225_gate = bool(
            node_l and node_l.artifacts.get("vdi2225", {}).get("gate_passed", False)
        )
        fmea_present = bool(
            node_t and "fmea" in node_t.artifacts
        )
        adr_generated = bool(node_e and node_e.adr_ref)
        lessons_count = 0
        if node_n:
            lines = [l.strip() for l in node_n.summary.splitlines() if l.strip()]
            lessons_count = sum(
                1 for l in lines if re.match(r'^[1-9\-\*•]\.*\s+', l)
            )
            if lessons_count == 0 and node_n.summary.strip():
                lessons_count = 1

        avg_confidence = (
            sum(s.confidence for s in case.steps) / len(case.steps)
            if case.steps else 0.0
        )
        rag_used = bool(
            node_s and node_s.artifacts.get("rag_context")
        )

        lessons_norm = min(lessons_count / 3.0, 1.0)
        overall = (
            completeness       * _WEIGHTS["spalten_completeness"]
            + avg_confidence   * _WEIGHTS["avg_confidence"]
            + float(vdi2225_gate) * _WEIGHTS["vdi2225_gate_passed"]
            + float(adr_generated) * _WEIGHTS["adr_generated"]
            + float(fmea_present)  * _WEIGHTS["fmea_present"]
            + lessons_norm     * _WEIGHTS["lessons_norm"]
            + float(rag_used)  * _WEIGHTS["rag_context_used"]
        )

        return {
            "spalten_completeness": round(completeness, 3),
            "vdi2225_gate_passed":  vdi2225_gate,
            "fmea_present":         fmea_present,
            "adr_generated":        adr_generated,
            "lessons_count":        lessons_count,
            "avg_confidence":       round(avg_confidence, 3),
            "rag_context_used":     rag_used,
            "overall_score":        round(overall, 3),
        }

    # ─── LLM-Judge ────────────────────────────────────────────────────────

    def llm_judge(self, case: EngineeringCase) -> Dict[str, Any]:
        """Ollama-LLM bewertet den SPALTEN-Durchlauf auf Skala 0.0-1.0."""
        summary = (
            f"Problem: {case.problem[:100]} | "
            f"Domain: {case.domain} | "
            f"Phasen: {len(case.steps)}/7 | "
            f"Loesung: {str(case.selected_solution or 'n/a')[:80]} | "
            f"Steps: {'; '.join(s.phase.name for s in case.steps)}"
        )[:500]

        payload = json.dumps({
            "model": JUDGE_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Du bist ein VDI-2225-Auditor. "
                        "Bewerte diesen SPALTEN-Durchlauf auf einer Skala 0.0-1.0. "
                        "Antworte NUR mit einer Zahl."
                    ),
                },
                {"role": "user", "content": summary},
            ],
            "options": {"temperature": 0.1},
            "stream": False,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data["message"]["content"].strip()
                match = re.search(r'(\d+(?:[.,]\d+)?)', raw)
                if match:
                    score = float(match.group(1).replace(",", "."))
                    score = max(0.0, min(1.0, score))
                else:
                    score = 0.5
                return {"llm_score": round(score, 3), "raw": raw}
        except Exception as e:
            return {"llm_score": 0.5, "raw": f"[FALLBACK] {e}"}

    # ─── ADR-Datei-Qualitaet ──────────────────────────────────────────────

    def evaluate_adr_file(self, filepath: Path) -> Dict[str, Any]:
        """Prueft Qualitaet einer einzelnen ADR-Markdown-Datei."""
        try:
            text = filepath.read_text(encoding="utf-8")
        except Exception as e:
            return {"error": str(e), "quality_score": 0.0}

        result: Dict[str, Any] = {"file": filepath.name}
        weighted_sum = 0.0

        for key, (needle, weight) in _ADR_CHECKS.items():
            present = needle in text
            result[key] = present
            if present:
                weighted_sum += weight

        result["quality_score"] = round(weighted_sum, 3)
        return result

    # ─── Alle ADRs evaluieren ─────────────────────────────────────────────

    def evaluate_all_adrs(self, adr_dir: Path) -> Dict[str, Any]:
        """Evaluiert alle .md Dateien in adr_dir und gibt Zusammenfassung zurueck."""
        files = sorted(adr_dir.glob("*.md"))
        if not files:
            return {"count": 0, "avg_quality": 0.0, "best": None, "worst": None, "details": []}

        details = [self.evaluate_adr_file(f) for f in files]
        scores = [d["quality_score"] for d in details]

        best = max(details, key=lambda d: d["quality_score"])
        worst = min(details, key=lambda d: d["quality_score"])
        avg = sum(scores) / len(scores)

        return {
            "count":       len(files),
            "avg_quality": round(avg, 3),
            "best":        best["file"],
            "best_score":  best["quality_score"],
            "worst":       worst["file"],
            "worst_score": worst["quality_score"],
            "details":     details,
        }
