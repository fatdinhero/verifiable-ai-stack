#!/usr/bin/env python3
"""
governance/models.py
Pydantic-Modelle für COGNITUM Governance + MPPS
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import uuid

class CaseStatus(str, Enum):
    draft = "draft"
    active = "active"
    blocked = "blocked"
    resolved = "resolved"
    archived = "archived"

class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class PlanningStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    complete = "complete"
    archived = "archived"

class ExperimentStatus(str, Enum):
    planning = "planning"
    running = "running"
    paused = "paused"
    complete = "complete"
    archived = "archived"

class ProblemSolvingCase(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {}})
    case_id: str = Field(default_factory=lambda: f"psc_{uuid.uuid4().hex[:8]}")
    title: str
    status: CaseStatus
    context: Dict[str, Any]
    problem_statement: Dict[str, Any]
    scope: Dict[str, Any] = Field(default_factory=dict)
    stakeholders: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    decision: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    learning: Dict[str, Any] = Field(default_factory=dict)
    audit: Dict[str, Any] = Field(default_factory=dict)

class PlanningSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"ps_{uuid.uuid4().hex[:8]}")
    title: str
    status: PlanningStatus
    context: Dict[str, Any]
    planning_brief: Dict[str, Any] = Field(default_factory=dict)
    customer_needs: Dict[str, Any] = Field(default_factory=dict)
    benchmark: Dict[str, Any] = Field(default_factory=dict)
    differentiation_profile: Dict[str, Any] = Field(default_factory=dict)
    concept_preparation: Dict[str, Any] = Field(default_factory=dict)
    concepts: List[Dict[str, Any]] = Field(default_factory=list)
    decision_prep: Dict[str, Any] = Field(default_factory=dict)
    post_planning: Dict[str, Any] = Field(default_factory=dict)
    audit: Dict[str, Any] = Field(default_factory=dict)

class ExperimentPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    title: str
    status: ExperimentStatus
    context: Dict[str, Any]
    hypothesis: Dict[str, Any]
    factors: Dict[str, Any] = Field(default_factory=dict)
    target_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    design: Dict[str, Any] = Field(default_factory=dict)
    execution: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    audit: Dict[str, Any] = Field(default_factory=dict)

class DecisionRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"dr_{uuid.uuid4().hex[:8]}")
    title: str
    context: Dict[str, Any]
    options_considered: List[Dict[str, Any]]
    decision: Dict[str, Any]
    rationale: Dict[str, Any]
    cfr_checks: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    audit: Dict[str, Any] = Field(default_factory=dict)

def create_opex_problem_solving_case(title: str, customer_issue: str) -> ProblemSolvingCase:
    return ProblemSolvingCase(
        title=title,
        status=CaseStatus.active,
        context={"domain": "opex_service", "product_or_service": "Fiverr Gig Package", "owner": "fatih"},
        problem_statement={"summary": customer_issue, "urgency": Urgency.medium},
        scope={"type": "service_delivery"},
        stakeholders=[{"role": "client"}],
        audit={"created_at": datetime.utcnow().isoformat() + "Z"}
    )

def create_cna_experiment_plan(hypothesis: str) -> ExperimentPlan:
    return ExperimentPlan(
        title=f"CNA Experiment: {hypothesis}",
        status=ExperimentStatus.planning,
        context={"domain": "cna_cli"},
        hypothesis={"statement": hypothesis},
        design={"type": "ml_doe", "adaptive": True},
        audit={"created_at": datetime.utcnow().isoformat() + "Z"}
    )