#!/usr/bin/env python3
"""
mpps_graph_blueprint.py
SPALTEN-StateGraph (LangGraph) für MPPS
"""

from typing import Annotated, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

class EngineeringState(dict):
    thread_id: str
    problem: str
    domain: str
    urgency: str
    current_phase: str
    situation: Dict[str, Any]
    problem_definition: Dict[str, Any]
    alternatives: list
    selected_solution: dict | None
    risk_assessment: dict
    implementation_plan: dict
    lessons_learned: list
    idea_pool: Annotated[list, operator.add]
    human_approved: bool
    audit_trail: list
    confidence: float
    requires_human: bool

def node_S(state: EngineeringState):
    return {"current_phase": "P", "situation": {"summary": f"Analysiert: {state['problem']}"}, "audit_trail": state.get("audit_trail", []) + [{"phase": "S"}]}

def node_P(state: EngineeringState):
    return {"current_phase": "A", "problem_definition": {"summary": "Eingegrenzt"}, "audit_trail": state.get("audit_trail", []) + [{"phase": "P"}]}

def node_A(state: EngineeringState):
    alts = state.get("alternatives", []) + [{"title": "Lösung A"}, {"title": "Lösung B"}]
    return {"current_phase": "L", "alternatives": alts, "idea_pool": alts, "audit_trail": state.get("audit_trail", []) + [{"phase": "A"}]}

def node_L(state: EngineeringState):
    return {"current_phase": "T", "selected_solution": {"title": "Beste Lösung", "score": 0.85}, "audit_trail": state.get("audit_trail", []) + [{"phase": "L"}]}

def node_T(state: EngineeringState):
    return {"current_phase": "E", "risk_assessment": {"high_risk": False}, "audit_trail": state.get("audit_trail", []) + [{"phase": "T"}]}

def node_E(state: EngineeringState):
    return {"current_phase": "N", "implementation_plan": {"steps": 5}}
    return {"current_phase": "N", "implementation_plan": {"steps": 5}, "audit_trail": state.get("audit_trail", []) + [{"phase": "E", "adr": "ADR-2026-05-04-001"}]}

def node_N(state: EngineeringState):
    return {"current_phase": "END", "lessons_learned": ["SPALTEN abgeschlossen"], "audit_trail": state.get("audit_trail", []) + [{"phase": "N"}]}

def should_continue(state: EngineeringState):
    if state["current_phase"] == "END":
        return END
    if state.get("requires_human") and not state.get("human_approved"):
        return "E"
    return state["current_phase"]

def build_spalten_graph():
    workflow = StateGraph(EngineeringState)
    workflow.add_node("S", node_S)
    workflow.add_node("P", node_P)
    workflow.add_node("A", node_A)
    workflow.add_node("L", node_L)
    workflow.add_node("T", node_T)
    workflow.add_node("E", node_E)
    workflow.add_node("N", node_N)
    workflow.set_entry_point("S")
    workflow.add_conditional_edges("S", should_continue)
    workflow.add_conditional_edges("P", should_continue)
    workflow.add_conditional_edges("A", should_continue)
    workflow.add_conditional_edges("L", should_continue)
    workflow.add_conditional_edges("T", should_continue)
    workflow.add_conditional_edges("E", should_continue)
    workflow.add_edge("N", END)
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)