#!/usr/bin/env python3
"""
COGNITUM Engineering Agent – SPALTEN Workflow mit Ollama (ADR-komplett)
"""
from __future__ import annotations
import uuid, json, sys, os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from pathlib import Path

import instructor
from openai import OpenAI
from pydantic import BaseModel, ConfigDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# ─── STATE ───────────────────────────────────────────────
class EngineeringState(TypedDict):
    thread_id: str
    problem: str
    domain: str
    urgency: str
    current_phase: str
    situation: Dict[str, Any]
    problem_definition: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    selected_solution: Optional[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    implementation_plan: Dict[str, Any]
    lessons_learned: List[str]
    idea_pool: Annotated[List[str], lambda x, y: x + y]
    human_approved: bool
    audit_trail: List[Dict[str, Any]]
    confidence: float
    requires_human: bool

# ─── LLM-BACKEND ─────────────────────────────────────────
_raw_client = OpenAI(
    base_url="https://api.xiaomimimo.com/v1",
    api_key=os.environ.get("MIMO_API_KEY"),
)
client = instructor.from_openai(_raw_client, mode=instructor.Mode.JSON)

class LLMOut(BaseModel):
    model_config = ConfigDict(extra="allow")

def call_llm(prompt: str) -> Dict[str, Any]:
    try:
        resp = client.chat.completions.create(
            model="mimo-v2.5-pro",
            response_model=LLMOut,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        return resp.model_dump(exclude_none=True)
    except Exception as e:
        return {"summary": f"Fehler: {e}"}

# ─── SPALTEN-NODES ───────────────────────────────────────
def ts():
    return datetime.now(timezone.utc).isoformat()

PHASE_PROMPTS = {
    "S": "Analysiere die Situation. Gib JSON mit 'summary' und 'stakeholders' zurueck.",
    "P": "Grenze das Problem ein. Gib JSON mit 'summary' und 'root_causes' zurueck.",
    "A": "Generiere 3-5 Loesungsalternativen. Gib JSON mit 'alternatives' (String-Liste) zurueck.",
    "T": "Fuehre FMEA durch. Gib JSON mit 'failure_modes' (Liste aus Objekten mit 'severity', 'occurrence', 'detection', 'failure_mode') zurueck.",
    "E": "Erstelle einen Umsetzungsplan. Gib JSON mit 'milestones' (String-Liste) zurueck.",
}

def node_S(state: EngineeringState) -> dict:
    result = call_llm(f"{PHASE_PROMPTS['S']} Problem: {state['problem']}")
    return {"situation": result, "current_phase": "P", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "S", "ts": ts(), "result": result}]}

def node_P(state: EngineeringState) -> dict:
    result = call_llm(f"{PHASE_PROMPTS['P']} Problem: {state['problem']}")
    return {"problem_definition": result, "current_phase": "A", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "P", "ts": ts(), "result": result}]}

def node_A(state: EngineeringState) -> dict:
    result = call_llm(f"{PHASE_PROMPTS['A']} Problem: {state['problem']}")
    raw = result.get("alternatives", ["Fallback"])
    return {"alternatives": state["alternatives"] + [{"title": a} if isinstance(a, str) else a for a in raw],
            "current_phase": "L", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "A", "ts": ts(), "result": result}]}

def node_L(state: EngineeringState) -> dict:
    if not state["alternatives"]:
        return {"selected_solution": {"title": "Fallback"}, "current_phase": "T", "confidence": 0.7}
    t = state["alternatives"][0]
    title = t if isinstance(t, str) else t.get("title", "Unbekannt")
    return {"selected_solution": {"title": title}, "current_phase": "T", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "L", "ts": ts(), "selected": title}]}

def node_T(state: EngineeringState) -> dict:
    result = call_llm(f"{PHASE_PROMPTS['T']} Loesung: {state.get('selected_solution', {}).get('title', 'N/A')}")
    return {"risk_assessment": result, "current_phase": "E", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "T", "ts": ts(), "result": result}]}

def node_E(state: EngineeringState) -> dict:
    result = call_llm(f"{PHASE_PROMPTS['E']} Loesung: {state.get('selected_solution', {}).get('title', 'N/A')}")
    return {"implementation_plan": result, "current_phase": "N", "confidence": 0.9,
            "audit_trail": state["audit_trail"] + [{"phase": "E", "ts": ts(), "result": result}]}

def node_N(state: EngineeringState) -> dict:
    return {"lessons_learned": ["SPALTEN abgeschlossen"], "current_phase": "END",
            "audit_trail": state["audit_trail"] + [{"phase": "N", "ts": ts()}]}

def router(state: EngineeringState) -> str:
    phase = state.get("current_phase", "END")
    return END if phase == "END" else phase

def route_after_T(state: EngineeringState) -> str:
    """T → immer E; kein human_approval-Gate in dieser Phase."""
    return "E"

def build_graph():
    wf = StateGraph(EngineeringState)
    for n, f in [("S", node_S), ("P", node_P), ("A", node_A), ("L", node_L), ("T", node_T), ("E", node_E), ("N", node_N)]:
        wf.add_node(n, f)
    wf.set_entry_point("S")
    for src in ["S", "P", "A", "L"]:
        wf.add_conditional_edges(src, router)
    wf.add_conditional_edges("T", route_after_T, {"E": "E"})
    wf.add_conditional_edges("E", router)
    wf.add_edge("N", END)
    return wf.compile(checkpointer=MemorySaver())

# ─── MAIN ────────────────────────────────────────────────
if __name__ == "__main__":
    problem = sys.argv[1] if len(sys.argv) > 1 else "CNA CLI Skalierungsproblem"
    domain = sys.argv[2] if len(sys.argv) > 2 else "cna_cli"

    graph = build_graph()
    state: EngineeringState = {
        "thread_id": str(uuid.uuid4()), "problem": problem, "domain": domain,
        "urgency": "high", "current_phase": "S", "situation": {}, "problem_definition": {},
        "alternatives": [], "selected_solution": None, "risk_assessment": {}, "implementation_plan": {},
        "lessons_learned": [], "idea_pool": [], "human_approved": True, "audit_trail": [],
        "confidence": 0.0, "requires_human": False
    }

    config = {"configurable": {"thread_id": state["thread_id"]}}
    full_state = {}
    for event in graph.stream(state, config):
        if isinstance(event, tuple):
            event = event[0]
        for node_name, node_output in event.items():
            print(f"✅ {node_name}", end=" → ", flush=True)
            if isinstance(node_output, dict):
                full_state.update(node_output)

    print("\n✅ SPALTEN-Durchlauf abgeschlossen.")

    # ADR speichern
    adr_dir = Path("docs/adr")
    adr_dir.mkdir(parents=True, exist_ok=True)
    adr_path = adr_dir / f"{datetime.now().strftime('%Y-%m-%d')}-{problem.lower().replace(' ', '-')[:30]}.json"
    with open(adr_path, "w") as f:
        json.dump(full_state, f, indent=2, ensure_ascii=False)
    print(f"📄 ADR gespeichert: {adr_path}")
