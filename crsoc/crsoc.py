#!/usr/bin/env python3
"""
crsoc/crsoc.py
CRSOCEngine — 8-Phasen Continuous Refinement & Synthesis of COGNITUM
Triggered alle 100 verarbeiteten Cases durch autonomous_loop.py
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.data_routing import (
    get_router,
    MIMO_BASE_URL,
    MIMO_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)

STATE_FILE    = REPO_ROOT / ".loop_state.json"
MASTERPLAN    = REPO_ROOT / "governance" / "masterplan.yaml"
BRIER_FILE    = REPO_ROOT / "reports" / "brier_history.json"


# ─── LLM Helper ──────────────────────────────────────────────────────────────

def _llm(prompt: str, max_tokens: int = 600) -> str:
    """Routet an MiMo oder Ollama je nach IP-Sensitivitaet."""
    backend = get_router(prompt)
    if backend == "mimo":
        url   = f"{MIMO_BASE_URL}/chat/completions"
        model = MIMO_MODEL
        auth  = f"Bearer {os.environ.get('MIMO_API_KEY', '')}"
    else:
        url   = f"{OLLAMA_BASE_URL}/chat/completions"
        model = OLLAMA_MODEL
        auth  = "Bearer ollama"

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "Authorization": auth},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
            # OpenAI-compat: choices[0].message.content
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LLM-FEHLER: {e}]"


def _load_loop_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_count": 0, "avg_score": 0.0, "scores": []}


def _load_masterplan_yaml() -> str:
    if MASTERPLAN.exists():
        try:
            return MASTERPLAN.read_text(encoding="utf-8")[:3000]
        except Exception:
            pass
    return ""


# ─── CRSOCEngine ─────────────────────────────────────────────────────────────

class CRSOCEngine:
    """8-Phasen CRSOC Vollzyklus."""

    def run_full_cycle(self, trigger: str) -> Dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        result: Dict[str, Any] = {
            "trigger":   trigger,
            "timestamp": ts,
            "phases":    {},
        }

        print(f"[CRSOC] === Zyklus START | trigger={trigger} | {ts} ===")

        # Phase 0 ─ Intake
        result["phases"]["0_intake"] = self._phase_0_intake()
        print(f"[CRSOC] Phase 0 abgeschlossen: {len(result['phases']['0_intake'])} Felder")

        # Phase 1 ─ Situation Analysis
        result["phases"]["1_situation"] = self._phase_1_situation(result["phases"]["0_intake"])
        print(f"[CRSOC] Phase 1: {result['phases']['1_situation'].get('summary', '')[:80]}")

        # Phase 2 ─ Morphological Mapping
        from crsoc.morphological_mapper import MorphologicalMapper
        mapper = MorphologicalMapper()
        result["phases"]["2_morphological"] = mapper.map(result["phases"]["1_situation"])
        print(f"[CRSOC] Phase 2: {len(result['phases']['2_morphological'].get('matrix', {}))} Dimensionen")

        # Phase 3 ─ Idealisierung
        from crsoc.idealisierung_engine import IdealisierungEngine
        engine = IdealisierungEngine()
        result["phases"]["3_ideas"] = engine.generate(result["phases"]["2_morphological"])
        print(f"[CRSOC] Phase 3: {len(result['phases']['3_ideas'].get('ideas', []))} Ideen generiert")

        # Phase 4 ─ Evaluation
        from crsoc.evaluation_metrics import EvaluationMetrics
        metrics = EvaluationMetrics()
        result["phases"]["4_evaluation"] = metrics.score(result["phases"]["3_ideas"])
        print(f"[CRSOC] Phase 4: Top-Score={result['phases']['4_evaluation'].get('top_score', 0):.2f}")

        # Phase 5 ─ MetaBell Validation (operator_psi → Ollama)
        result["phases"]["5_metabell"] = self._phase_5_metabell(result["phases"]["4_evaluation"])
        passed = result["phases"]["5_metabell"].get("passed", 0)
        print(f"[CRSOC] Phase 5: {passed} Ideen bestehen operator_psi > 1.4")

        # Phase 6 ─ Masterplan Update + ADR
        from crsoc.masterplan_updater import MasterplanUpdater
        updater = MasterplanUpdater()
        result["phases"]["6_masterplan"] = updater.update(
            result["phases"]["5_metabell"].get("validated_ideas", []),
            result,
        )
        print(f"[CRSOC] Phase 6: ADR={result['phases']['6_masterplan'].get('adr_path', 'n/a')}")

        # Phase 7 ─ Temporal Feedback (Brier Score)
        from crsoc.temporal_feedback import TemporalFeedback
        tf = TemporalFeedback()
        result["phases"]["7_temporal"] = tf.compute(result["phases"]["4_evaluation"])
        print(f"[CRSOC] Phase 7: Brier={result['phases']['7_temporal'].get('brier_score', 'n/a')}")

        # Best idea summary
        best = result["phases"]["5_metabell"].get("best_idea", {})
        result["best_idea"]  = best.get("name", "—")
        result["best_score"] = best.get("psi_score", 0.0)
        result["adr_path"]   = result["phases"]["6_masterplan"].get("adr_path", "")

        print(f"[CRSOC] === Zyklus ENDE | beste Idee: {result['best_idea']} (Ψ={result['best_score']:.2f}) ===")
        return result

    # ── Phase 0 ───────────────────────────────────────────────────────────────

    def _phase_0_intake(self) -> Dict[str, Any]:
        state    = _load_loop_state()
        mp_yaml  = _load_masterplan_yaml()
        scores   = state.get("scores", [])
        recent   = scores[-50:] if len(scores) >= 50 else scores
        return {
            "processed_count": state.get("processed_count", 0),
            "avg_score":       state.get("avg_score", 0.0),
            "recent_avg":      round(sum(recent) / len(recent), 4) if recent else 0.0,
            "skipped_count":   state.get("skipped_count", 0),
            "masterplan_excerpt": mp_yaml[:500],
            "last_run":        state.get("last_run", "unknown"),
        }

    # ── Phase 1 ───────────────────────────────────────────────────────────────

    def _phase_1_situation(self, intake: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            f"Du analysierst den Stand eines autonomen Engineering-Systems nach VDI 2221.\n\n"
            f"Kennzahlen:\n"
            f"- Verarbeitete Cases: {intake['processed_count']}\n"
            f"- Gesamt-Avg-Score: {intake['avg_score']}\n"
            f"- Letzte-50-Avg-Score: {intake['recent_avg']}\n"
            f"- Uebersprungen: {intake['skipped_count']}\n\n"
            f"Fasse die Situation in 3 Saetzen zusammen und nenne 2 konkrete Verbesserungspotentiale. "
            f"Antworte als JSON mit Feldern: summary (String), improvements (String-Liste)."
        )
        raw = _llm(prompt, max_tokens=400)
        try:
            data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        except Exception:
            data = {"summary": raw[:200], "improvements": []}
        data["intake_ref"] = intake
        return data

    # ── Phase 5 ───────────────────────────────────────────────────────────────

    def _phase_5_metabell(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        ideas = evaluation.get("scored_ideas", [])
        if not ideas:
            return {"passed": 0, "validated_ideas": [], "best_idea": {}}

        # operator_psi im Prompt → get_router() → "ollama"
        prompt = (
            "Bewerte folgende Engineering-Ideen mit dem operator_psi Qualitaetsoperator.\n"
            "operator_psi = (impact * novelty) / (1 + complexity)\n"
            "Schwellenwert: operator_psi > 1.4 = bestanden.\n\n"
            "Ideen (JSON-Liste):\n" + json.dumps(ideas[:8], ensure_ascii=False) + "\n\n"
            "Antworte als JSON: validated (Liste mit {name, operator_psi, passed})"
        )
        raw = _llm(prompt, max_tokens=600)
        try:
            parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
            validated = parsed.get("validated", [])
        except Exception:
            # Fallback: berechne operator_psi direkt aus scores
            validated = []
            for idea in ideas[:8]:
                impact     = idea.get("impact_score", 0.5)
                novelty    = idea.get("novelty_score", 0.5)
                complexity = idea.get("complexity", 1.0)
                # Ψ = (impact + novelty) / (1 + complexity) → Range 0..2
                psi        = round((impact + novelty) / (1 + complexity), 3)
                validated.append({
                    "name":        idea.get("name", "Unbekannt"),
                    "operator_psi": psi,
                    "passed":      psi > 1.4,
                })

        passed_list = [v for v in validated if v.get("passed") or v.get("operator_psi", 0) > 1.4]
        best = max(validated, key=lambda x: x.get("operator_psi", 0)) if validated else {}
        # Rename for export
        if best:
            best["psi_score"] = best.get("operator_psi", 0)

        return {
            "passed":          len(passed_list),
            "validated_ideas": validated,
            "best_idea":       best,
            "threshold":       1.4,
        }
