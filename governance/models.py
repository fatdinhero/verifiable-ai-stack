"""
governance/models.py
Pydantic-Modelle fuer COGNITUM Engineering Agent
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class CaseStatus(str, Enum):
    draft = "draft"
    active = "active"
    blocked = "blocked"
    resolved = "resolved"

class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class SPALTENPhase(str, Enum):
    S = "situationsanalyse"
    P = "problemeingrenzung"
    A = "alternativen"
    L = "loesungsauswahl"
    T = "tragweitenanalyse"
    E = "entscheiden"
    N = "nachbereiten"

class StepResult(BaseModel):
    phase: SPALTENPhase
    summary: str
    detail: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    unverified: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    adr_ref: Optional[str] = None

class EngineeringCase(BaseModel):
    case_id: str = Field(default_factory=lambda: f"eng_{uuid.uuid4().hex[:8]}")
    title: str
    problem: str
    domain: str = "general"
    urgency: Urgency = Urgency.medium
    status: CaseStatus = CaseStatus.active
    steps: List[StepResult] = Field(default_factory=list)
    idea_pool: List[str] = Field(default_factory=list)
    selected_solution: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
