#!/usr/bin/env python3
"""
run_revenue_spalten.py
COGNITUM Revenue-Pfad SPALTEN-Analyse 2026
Angepasste Morphologie-Matrix + VDI 2225 Gewichte fuer Revenue-Optimierung
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from typing import List, Dict, Any
from datetime import datetime

from governance.registry import (
    get_action_priority, calculate_rpn,
    vdi2225_evaluate, morphologischer_kasten,
)
from governance.models import StepResult, SPALTENPhase, EngineeringCase
import spalten_agent as _base

# ═══════════════════════════════════════════
# Angepasste Morphologie-Matrix (node_A)
# ═══════════════════════════════════════════
REVENUE_MATRIX = {
    "Kanal":        ["JetBrains Marketplace", "Gumroad", "Skywork-Partnership",
                     "MCP-Registry", "Direct B2B"],
    "Zeithorizont": ["sofort (<4 Wochen)", "kurzfristig (1-3 Monate)",
                     "mittelfristig (3-6 Monate)"],
    "Zielgruppe":   ["Solo-Entwickler", "DACH-Mittelstand",
                     "Internationale ML-Teams", "Enterprise"],
    "Aufwand":      ["minimal", "mittel", "hoch"],
}

# 5 Representative Varianten — eine pro Kanal (Cover der 3 Kernpfade + 2 Alternativen)
REVENUE_VARIANTEN = [
    {"Kanal": "JetBrains Marketplace", "Zeithorizont": "sofort (<4 Wochen)",
     "Zielgruppe": "Solo-Entwickler", "Aufwand": "minimal"},
    {"Kanal": "Gumroad", "Zeithorizont": "sofort (<4 Wochen)",
     "Zielgruppe": "Solo-Entwickler", "Aufwand": "minimal"},
    {"Kanal": "Skywork-Partnership", "Zeithorizont": "mittelfristig (3-6 Monate)",
     "Zielgruppe": "Internationale ML-Teams", "Aufwand": "mittel"},
    {"Kanal": "MCP-Registry", "Zeithorizont": "kurzfristig (1-3 Monate)",
     "Zielgruppe": "Solo-Entwickler", "Aufwand": "minimal"},
    {"Kanal": "Direct B2B", "Zeithorizont": "mittelfristig (3-6 Monate)",
     "Zielgruppe": "DACH-Mittelstand", "Aufwand": "hoch"},
]

# ═══════════════════════════════════════════
# Angepasste VDI 2225 Gewichte (node_L)
# ═══════════════════════════════════════════
REVENUE_GEWICHTE = {
    "revenue_speed":      0.35,
    "aufwand":            0.30,
    "strategische_tiefe": 0.20,
    "skalierbarkeit":     0.15,
}

# Deterministischer Score pro Variante (1=schlecht, 4=sehr gut)
# Begruendung:
#   V1 JetBrains: schnell deploybar, dev-Audience, wenig Aufwand, begrenzte Tiefe
#   V2 Gumroad:   sofort live, kein Gating, minimal Aufwand, limitierte Skalierung
#   V3 Skywork:   langsam, Partneraufwand hoch, aber maximale ML-Tiefe + Enterprise-Scale
#   V4 MCP-Registry: mittelfristig, LLM-native Zielgruppe, Netzwerkeffekte
#   V5 Direct B2B:  hoeher Aufwand, langsam, aber tiefste strategische Bindung
REVENUE_SCORES = {
    "V1": {"revenue_speed": 3, "aufwand": 4, "strategische_tiefe": 2, "skalierbarkeit": 3},
    "V2": {"revenue_speed": 4, "aufwand": 4, "strategische_tiefe": 2, "skalierbarkeit": 2},
    "V3": {"revenue_speed": 1, "aufwand": 2, "strategische_tiefe": 4, "skalierbarkeit": 4},
    "V4": {"revenue_speed": 2, "aufwand": 3, "strategische_tiefe": 3, "skalierbarkeit": 4},
    "V5": {"revenue_speed": 2, "aufwand": 1, "strategische_tiefe": 4, "skalierbarkeit": 3},
}


def node_A_revenue(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Revenue-angepasster Morphologischer Kasten."""
    varianten_text = "\n".join(
        f"V{i+1}: Kanal={v['Kanal']}, Zeithorizont={v['Zeithorizont']}, "
        f"Zielgruppe={v['Zielgruppe']}, Aufwand={v['Aufwand']}"
        for i, v in enumerate(REVENUE_VARIANTEN)
    )
    prompt = (
        f"Problem-Statement: {prev.summary}\n\n"
        f"Revenue-Pfade aus Morphologischem Kasten:\n{varianten_text}\n\n"
        "Bewerte JEDEN Pfad (V1 bis V5) mit genau 1 Satz: "
        "nenne den Hauptvorteil fuer COGNITUM 2026 und das groesste Risiko."
    )
    llm_bewertung = _base.call_llm(prompt)

    for i, var in enumerate(REVENUE_VARIANTEN):
        case.idea_pool.append(f"V{i+1}: {var}")

    return StepResult(
        phase=SPALTENPhase.A,
        summary=(
            f"Revenue-Morphologie: {len(REVENUE_VARIANTEN)} Pfade analysiert.\n"
            f"{llm_bewertung}"
        ),
        confidence=0.82,
        artifacts={"morphologie_matrix": REVENUE_MATRIX, "varianten": REVENUE_VARIANTEN},
    )


def node_L_revenue(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Revenue-VDI-2225-Auswertung mit angepassten Gewichten."""
    varianten = prev.artifacts.get("varianten", [])
    if not varianten:
        return StepResult(
            phase=SPALTENPhase.L,
            summary="Keine Varianten — Ruecksprung zu A",
            confidence=0.3,
            artifacts={"ruecksprung": True},
        )

    vdi_result = vdi2225_evaluate(REVENUE_SCORES, REVENUE_GEWICHTE, skala_max=4, mindest_score=0.6)
    best = vdi_result["best"]
    best_score = vdi_result["best_score"]

    # Sieger-Variante in Case speichern
    best_idx = int(best[1:]) - 1
    if best_idx < len(varianten):
        case.selected_solution = str(varianten[best_idx])

    varianten_text = "\n".join(
        f"V{i+1} ({v['Kanal']}): Score={vdi_result['scores'].get(f'V{i+1}', 0):.4f}"
        for i, v in enumerate(varianten[:5])
    )
    prompt = (
        f"VDI 2225-Auswertung (Gewichte: revenue_speed=0.35, aufwand=0.30, "
        f"strategische_tiefe=0.20, skalierbarkeit=0.15):\n\n"
        f"Scores:\n{varianten_text}\n\n"
        f"Sieger: {best} mit Score {best_score:.4f}.\n\n"
        "Begruende in genau 2 Saetzen, warum dieser Revenue-Pfad fuer COGNITUM 2026 optimal ist. "
        "Nenne auch den zweitbesten Pfad als Backup-Option."
    )
    llm_rationale = _base.call_llm(prompt)

    return StepResult(
        phase=SPALTENPhase.L,
        summary=(
            f"VDI 2225 Revenue-Auswertung:\n"
            f"  Beste Option : {best} Score={best_score:.4f} "
            f"Gate={'PASS' if vdi_result['gate_passed'] else 'FAIL'}\n"
            f"  Alle Scores  : {json.dumps(vdi_result['scores'], indent=2)}\n"
            f"\nLLM-Begruendung:\n{llm_rationale}"
        ),
        confidence=0.93 if vdi_result["gate_passed"] else 0.45,
        artifacts={"vdi2225": vdi_result, "llm_rationale": llm_rationale,
                   "gewichte": REVENUE_GEWICHTE},
    )


def run_revenue_analysis():
    """Fuehrt Revenue-SPALTEN durch mit angepassten node_A und node_L."""
    case = EngineeringCase(
        title="COGNITUM Revenue-Pfad 2026",
        problem=(
            "Welcher Revenue-Pfad hat maximalen Impact fuer COGNITUM 2026: "
            "JetBrains Marketplace Plugin, Skywork-Partnerschaft, oder Gumroad-Produkt?"
        ),
        domain="cognitum",
    )

    # Patch: Ersetze node_A und node_L mit Revenue-Varianten
    custom_nodes = [
        ("S", _base.node_S),
        ("P", _base.node_P),
        ("A", node_A_revenue),
        ("L", node_L_revenue),
        ("T", _base.node_T),
        ("E", _base.node_E),
        ("N", _base.node_N),
    ]

    human_approve = True
    skip_gitops = False

    print(f"\n{'='*65}")
    print(f"COGNITUM REVENUE SPALTEN-ANALYSE 2026")
    print(f"Problem: {case.problem}")
    print(f"Morphologie: {list(REVENUE_MATRIX.keys())}")
    print(f"VDI-Gewichte: {REVENUE_GEWICHTE}")
    print(f"{'='*65}\n")

    prev_result = None
    e_executed = False

    for label, node_fn in custom_nodes:
        print(f"[{label}] {SPALTENPhase[label].value}...")

        if label == "E" and not human_approve:
            print("  ⏸  human_approve=False — E wird uebersprungen (ADR via skip_gitops=False nach N)")
            break

        result = node_fn(case) if prev_result is None else node_fn(case, prev_result)
        case.steps.append(result)
        prev_result = result

        if label == "E":
            e_executed = True

        if label == "L" and result.artifacts.get("ruecksprung"):
            print("  Ruecksprung zu A ausgeloest")
            continue

        print(f"  Confidence: {result.confidence:.2f}")
        if result.artifacts:
            keys = [k for k in result.artifacts if k != "varianten"]
            print(f"  Artefakte: {keys}")
        print(f"  Summary:\n    {result.summary[:300].replace(chr(10), chr(10)+'    ')}")
        print()

    # GitOps: laeuft nur wenn E ausgefuehrt + skip_gitops=False
    if human_approve and e_executed and not skip_gitops:
        _base._trigger_gitops(case)

    # RAG
    _base._store_in_rag(case)

    avg_conf = sum(s.confidence for s in case.steps) / max(len(case.steps), 1)

    print(f"\n{'='*65}")
    print(f"SPALTEN ABGESCHLOSSEN | Schritte: {len(case.steps)} | O Confidence: {avg_conf:.2f}")
    print(f"{'='*65}")

    # VDI 2225 Detailausgabe
    node_l = next((s for s in case.steps if s.phase == SPALTENPhase.L), None)
    if node_l:
        vdi = node_l.artifacts.get("vdi2225", {})
        gewichte = node_l.artifacts.get("gewichte", REVENUE_GEWICHTE)
        rationale = node_l.artifacts.get("llm_rationale", "")

        print(f"\n{'─'*65}")
        print("VDI 2225 REVENUE-MATRIX ERGEBNIS")
        print(f"{'─'*65}")
        print(f"Gewichte: revenue_speed={gewichte['revenue_speed']:.2f}  "
              f"aufwand={gewichte['aufwand']:.2f}  "
              f"strategische_tiefe={gewichte['strategische_tiefe']:.2f}  "
              f"skalierbarkeit={gewichte['skalierbarkeit']:.2f}")
        print()
        print(f"{'Variante':<8} {'Kanal':<25} {'Score':>8}  {'Gate':<6}")
        print(f"{'─'*55}")
        scores = vdi.get("scores", {})
        best = vdi.get("best", "?")
        for i, var in enumerate(REVENUE_VARIANTEN):
            vn = f"V{i+1}"
            sc = scores.get(vn, 0)
            kanal = var["Kanal"]
            gate = "PASS" if sc >= 0.6 else "FAIL"
            marker = " <-- WINNER" if vn == best else ""
            print(f"{vn:<8} {kanal:<25} {sc:>8.4f}  {gate:<6}{marker}")
        print(f"{'─'*55}")
        print(f"\nSIEGER: {best} = {REVENUE_VARIANTEN[int(best[1:])-1]['Kanal']}")
        print(f"Score: {vdi.get('best_score', 0):.4f}  Gate: {'PASS' if vdi.get('gate_passed') else 'FAIL'}")
        print(f"\nLLM-BEGRUENDUNG:\n{rationale}")

    # Evaluator
    if _base._evaluator:
        try:
            eval_result = _base._evaluator.evaluate_case(case)
            print(f"\n{'─'*65}")
            print("SPALTEN EVALUATOR")
            print(f"{'─'*65}")
            print(f"  Overall Score : {eval_result['overall_score']:.2f}")
            print(f"  Completeness  : {eval_result['spalten_completeness']:.2f}")
            print(f"  Avg Confidence: {eval_result['avg_confidence']:.2f}")
            print(f"  VDI2225 Gate  : {'PASS' if eval_result['vdi2225_gate_passed'] else 'FAIL'}")
            print(f"  Lessons       : {eval_result['lessons_count']}")
        except Exception as e:
            print(f"  Evaluierung: {e}")

    _base._export_json(case)
    return case


if __name__ == "__main__":
    run_revenue_analysis()
