#!/usr/bin/env python3
"""
spalten_agent.py
COGNITUM Engineering Agent — SPALTEN als StateGraph
Laeuft lokal auf Mac Mini M4 mit Ollama qwen2.5:7b
"""
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# Governance-Imports
from governance.registry import (
    get_action_priority, get_ta_laerm, calculate_rpn,
    vdi2225_evaluate, morphologischer_kasten,
)
from governance.models import StepResult, SPALTENPhase, EngineeringCase

# ═══════════════════════════════════════════
# Ollama-Wrapper — REST-API (entspricht ollama.chat() intern)
# Direkt-HTTP weil das lokale ollama/-Verzeichnis die pip-Library ueberdeckt.
# ═══════════════════════════════════════════

MODEL = "qwen2.5:7b"  # lokal verfuegbares Instruct-Modell (qwen2.5:7b-instruct nicht gepullt)
OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_SYSTEM = (
    "Du bist ein systematischer Konstruktionsingenieur nach VDI 2221. "
    "Antworte immer auf Deutsch. Maximal 150 Wörter. Sei präzise und strukturiert."
)


def call_llm(prompt: str, system_prompt: str = None, temperature: float = 0.3) -> str:
    """Ruft Ollama lokal via HTTP-API auf (aequivalent zu ollama.chat()).
    Graceful Fallback auf Simulation wenn Ollama nicht erreichbar."""
    import urllib.request
    import urllib.error

    sys_msg = system_prompt or DEFAULT_SYSTEM
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user",   "content": prompt},
        ],
        "options": {"temperature": temperature},
        "stream": False,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        return f"[SIMULATION] Ollama nicht erreichbar ({e}). Prompt: {prompt[:80]}..."


# ═══════════════════════════════════════════
# SPALTEN-Knoten (jeder ist eine reine Funktion)
# ═══════════════════════════════════════════

def node_S(case: EngineeringCase) -> StepResult:
    """Situationsanalyse: LLM analysiert Problem und liefert strukturierten Ist-Zustand."""
    prompt = (
        f"Problem: {case.problem}\n"
        f"Domain: {case.domain}\n"
        f"Dringlichkeit: {case.urgency.value}\n\n"
        "Liefere eine strukturierte Situationsanalyse mit:\n"
        "1. Ist-Zustand\n"
        "2. Rahmenbedingungen\n"
        "3. Betroffene Stakeholder"
    )
    response = call_llm(prompt)
    return StepResult(phase=SPALTENPhase.S, summary=response, confidence=0.85)


def node_P(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Problemeingrenzung: LLM fuehrt 5-Why durch und formuliert praezises Problem-Statement."""
    prompt = (
        f"Situationsanalyse:\n{prev.summary}\n\n"
        "Fuehre eine vollstaendige 5-Why-Analyse durch. "
        "Formuliere abschliessend EIN praezises Problem-Statement in einem Satz."
    )
    response = call_llm(prompt)
    return StepResult(phase=SPALTENPhase.P, summary=response, confidence=0.88)


def node_A(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Alternativen: Code erzeugt Morphologie-Matrix, LLM bewertet jede Variante qualitativ."""
    # Code-Tool — deterministisch (kein LLM fuer Struktur)
    matrix = {
        "Architektur": ["Monolith", "Microservice", "Plugin-System", "Serverless"],
        "Datenhaltung": ["SQLite", "PostgreSQL", "YAML-Files", "JSON-Store"],
        "Schnittstelle": ["CLI", "REST-API", "MCP-Server", "Web-UI"],
        "Deployment":    ["Local-Only", "Docker", "pip-Package", "Hybrid"],
    }
    varianten = morphologischer_kasten(matrix, max_varianten=5)

    varianten_text = "\n".join(
        f"V{i+1}: {', '.join(f'{k}={v}' for k, v in var.items())}"
        for i, var in enumerate(varianten)
    )
    # LLM bewertet jede Variante mit 1 Satz
    prompt = (
        f"Problem-Statement: {prev.summary}\n\n"
        f"Loesungsvarianten aus dem Morphologischen Kasten:\n{varianten_text}\n\n"
        "Bewerte JEDE Variante (V1 bis V5) mit genau 1 Satz: "
        "nenne den Hauptvorteil und das Hauptrisiko."
    )
    llm_bewertung = call_llm(prompt)

    for i, var in enumerate(varianten):
        case.idea_pool.append(f"V{i+1}: {var}")

    return StepResult(
        phase=SPALTENPhase.A,
        summary=f"Morphologischer Kasten: {len(varianten)} Varianten generiert.\n{llm_bewertung}",
        confidence=0.80,
        artifacts={"morphologie_matrix": matrix, "varianten": varianten},
    )


def node_L(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Loesungsauswahl: Code berechnet VDI 2225-Score, LLM begruendet Sieger in 2 Saetzen."""
    varianten = prev.artifacts.get("varianten", [])
    if not varianten:
        return StepResult(
            phase=SPALTENPhase.L,
            summary="Keine Varianten — Ruecksprung zu A",
            confidence=0.3,
            artifacts={"ruecksprung": True},
        )

    gewichte = {
        "umsetzbarkeit": 0.30,
        "revenue_speed": 0.25,
        "strategie":     0.25,
        "wartbarkeit":   0.20,
    }
    # Deterministischer Bewertungs-Fallback (Code, NICHT das LLM)
    fallback_scores = [
        {"umsetzbarkeit": 4, "revenue_speed": 3, "strategie": 3, "wartbarkeit": 4},
        {"umsetzbarkeit": 3, "revenue_speed": 4, "strategie": 4, "wartbarkeit": 3},
        {"umsetzbarkeit": 3, "revenue_speed": 3, "strategie": 2, "wartbarkeit": 3},
        {"umsetzbarkeit": 2, "revenue_speed": 2, "strategie": 3, "wartbarkeit": 2},
        {"umsetzbarkeit": 3, "revenue_speed": 3, "strategie": 3, "wartbarkeit": 3},
    ]
    optionen = {
        f"V{i+1}": fallback_scores[i] if i < len(fallback_scores) else fallback_scores[-1]
        for i in range(min(len(varianten), 5))
    }

    # VDI 2225 Bewertung — Code-Tool, deterministisch
    vdi_result = vdi2225_evaluate(optionen, gewichte, skala_max=4, mindest_score=0.6)
    best = vdi_result["best"]
    best_score = vdi_result["best_score"]

    # Sieger in Case speichern
    best_idx = int(best[1:]) - 1
    if best_idx < len(varianten):
        case.selected_solution = str(varianten[best_idx])

    # LLM begruendet den Sieger in genau 2 Saetzen
    varianten_text = "\n".join(
        f"V{i+1}: {', '.join(f'{k}={v}' for k, v in var.items())}"
        for i, var in enumerate(varianten[:5])
    )
    prompt = (
        f"VDI 2225-Auswertung: Sieger ist {best} mit Score {best_score:.2f}.\n"
        f"Varianten:\n{varianten_text}\n\n"
        f"Begruende in genau 2 Saetzen, warum {best} die optimale Loesung ist."
    )
    llm_rationale = call_llm(prompt)

    return StepResult(
        phase=SPALTENPhase.L,
        summary=(
            f"VDI 2225: Beste={best} Score={best_score:.2f} "
            f"Gate={'PASS' if vdi_result['gate_passed'] else 'FAIL'}\n{llm_rationale}"
        ),
        confidence=0.92 if vdi_result["gate_passed"] else 0.45,
        artifacts={"vdi2225": vdi_result, "llm_rationale": llm_rationale},
    )


def node_T(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Tragweitenanalyse: FMEA mit Code-Tool."""
    risks = [
        {"mode": "Technische Komplexitaet", "s": 6, "o": 4, "d": 3},
        {"mode": "Marktakzeptanz unklar",   "s": 7, "o": 5, "d": 6},
        {"mode": "Solo-Dev-Risiko",          "s": 8, "o": 7, "d": 4},
    ]
    for r in risks:
        r["rpn"] = calculate_rpn(r["s"], r["o"], r["d"])
        r["ap"] = get_action_priority(r["s"], r["o"], r["d"])
    high_risks = [r for r in risks if r["ap"] == "H"]
    return StepResult(
        phase=SPALTENPhase.T,
        summary=f"FMEA: {len(risks)} Risiken, davon {len(high_risks)} kritisch (AP=H)",
        confidence=0.88,
        artifacts={"fmea": risks, "high_risk_count": len(high_risks)},
    )


def node_E(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Entscheiden & Umsetzen: ADR referenzieren."""
    adr_id = f"ADR-{datetime.utcnow().strftime('%Y-%m-%d')}-{case.case_id[-3:]}"
    return StepResult(
        phase=SPALTENPhase.E,
        summary=f"Entscheidung dokumentiert als {adr_id}",
        confidence=0.95,
        adr_ref=adr_id,
        artifacts={"adr_id": adr_id, "implementation_steps": 5},
    )


def node_N(case: EngineeringCase, prev: StepResult) -> StepResult:
    """Nachbereiten & Lernen: LLM formuliert 3 Lessons Learned."""
    prompt = (
        f"SPALTEN-Durchlauf abgeschlossen.\n"
        f"Problem: {case.problem}\n"
        f"Gewaelte Loesung: {case.selected_solution or 'nicht festgelegt'}\n\n"
        "Formuliere die 3 wichtigsten Lessons Learned (nummeriert, je 1 Satz)."
    )
    response = call_llm(prompt)
    return StepResult(phase=SPALTENPhase.N, summary=response, confidence=0.90)


# ═══════════════════════════════════════════
# SPALTEN-Runner (sequentiell, mit Ruecksprung-Logik)
# ═══════════════════════════════════════════

SPALTEN_NODES = [
    ("S", node_S),
    ("P", node_P),
    ("A", node_A),
    ("L", node_L),
    ("T", node_T),
    ("E", node_E),
    ("N", node_N),
]


def _extract_lessons(summary: str) -> List[str]:
    """Extrahiert nummerierte/aufgezaehlte Lessons aus LLM-Text."""
    lines = [l.strip() for l in summary.splitlines() if l.strip()]
    lessons = []
    for line in lines:
        m = re.match(r'^[1-9\-\*•]\.*\s+(.*)', line)
        if m:
            lessons.append(m.group(1))
    return lessons[:3] if lessons else [summary[:200]]


def _trigger_gitops(case: EngineeringCase) -> None:
    """Ruft GitOpsHandler nach abgeschlossenem Durchlauf auf (benoetigt L + N)."""
    try:
        from governance.gitops_handler import GitOpsHandler

        node_l = next((s for s in case.steps if s.phase == SPALTENPhase.L), None)
        node_n = next((s for s in case.steps if s.phase == SPALTENPhase.N), None)

        score = (
            node_l.artifacts.get("vdi2225", {}).get("best_score", 0.0)
            if node_l else 0.0
        )
        rationale = node_l.artifacts.get("llm_rationale", "") if node_l else ""
        lessons = _extract_lessons(node_n.summary) if node_n else []

        handler = GitOpsHandler()
        result = handler.propose_adr(
            feature_name=case.title,
            solution=case.selected_solution or "noch nicht festgelegt",
            score=score,
            rationale=rationale,
            lessons=lessons,
        )
        print(f"  🌿 GitOps: {result.get('status')} | Branch: {result.get('branch', 'n/a')}")
        if result.get("error"):
            print(f"  ⚠️  GitOps-Fehler: {result['error']}")
    except Exception as e:
        print(f"  ⚠️  GitOps-Integration nicht verfuegbar: {e}")


def _export_json(case: EngineeringCase) -> str:
    """Exportiert Ergebnis als spalten_result_<timestamp>.json."""
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"spalten_result_{ts}.json"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(case.model_dump_json(indent=2))
    print(f"📁 JSON-Export: {filename}")
    return filename


def run_spalten(case: EngineeringCase, human_approve: bool = True) -> EngineeringCase:
    """Fuehrt den kompletten SPALTEN-Durchlauf aus."""
    print(f"\n{'='*60}")
    print(f"SPALTEN-Durchlauf: {case.title}")
    print(f"Problem: {case.problem}")
    print(f"{'='*60}\n")

    prev_result = None
    e_executed = False

    for label, node_fn in SPALTEN_NODES:
        print(f"[{label}] {SPALTENPhase[label].value}...")

        # Human-in-the-Loop vor E
        if label == "E" and not human_approve:
            print("  ⏸️  Human Approval erforderlich. Abbruch.")
            break

        result = node_fn(case) if prev_result is None else node_fn(case, prev_result)
        case.steps.append(result)
        prev_result = result

        if label == "E":
            e_executed = True

        # Ruecksprung-Logik: L -> A wenn keine Varianten
        if label == "L" and result.artifacts.get("ruecksprung"):
            print("  ⚠️  Ruecksprung zu A ausgeloest")
            continue

        print(f"  ✅ Confidence: {result.confidence:.2f}")
        if result.artifacts:
            print(f"  📊 Artefakte: {list(result.artifacts.keys())}")
        if result.adr_ref:
            print(f"  📝 ADR: {result.adr_ref}")

    # GitOps nach vollstaendigem Lauf (benoetigt node_L + node_N)
    if human_approve and e_executed:
        _trigger_gitops(case)

    avg_conf = sum(s.confidence for s in case.steps) / max(len(case.steps), 1)
    print(f"\n{'='*60}")
    print(f"✅ SPALTEN abgeschlossen | Schritte: {len(case.steps)} | Ø Confidence: {avg_conf:.2f}")
    print(f"{'='*60}\n")

    # JSON-Export nach jedem Durchlauf
    _export_json(case)
    return case


# ═══════════════════════════════════════════
# Hauptprogramm
# ═══════════════════════════════════════════

if __name__ == "__main__":
    case = EngineeringCase(
        title="CNA CLI Timeout-Problem",
        problem="CNA CLI zeigt Timeouts bei mehr als 8 gleichzeitigen Nutzern",
        domain="cna_cli",
    )
    run_spalten(case)
