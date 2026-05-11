from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class Status(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"

class LinkSet(BaseModel):
    upstream: List[str] = Field(default_factory=list)
    downstream: List[str] = Field(default_factory=list)

class ConstitutionArticle(BaseModel):
    id: int = Field(..., ge=1)
    title: str
    text: str

class ADR(BaseModel):
    id: str = Field(..., pattern=r"^ADR-\d{4}-\d{2}-\d{2}-\d{3}$")
    title: str
    status: Status
    date: str
    context: str
    decision: str
    consequences: str
    links: LinkSet = Field(default_factory=LinkSet)
    superseded_by: Optional[str] = None
    morphologischer_kasten: Optional[Dict[str, Any]] = None
    bewertungsmatrix: Optional[Dict[str, Any]] = None

class SensorRequirement(BaseModel):
    sensor: str
    required: bool = False
    consent: bool = False

class NormRule(BaseModel):
    id: str
    description: str
    sensor_requirements: List[SensorRequirement] = Field(default_factory=list)
    condition_yaml: str

class Module(BaseModel):
    id: str
    name: str
    version: str
    status: Status
    description: str
    layer: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    validation: str = ""
    links: LinkSet = Field(default_factory=LinkSet)
    norms: Optional[List[NormRule]] = None
    coverage: Optional[float] = None
    tests: Optional[int] = None

class Iso25010SubCharacteristic(BaseModel):
    name: str
    status: Status
    test_marker: Optional[str] = None
    notes: Optional[str] = None

class Iso25010Characteristic(BaseModel):
    name: str
    sub_characteristics: List[Iso25010SubCharacteristic] = Field(default_factory=list)

class RiskItem(BaseModel):
    id: str
    description: str
    probability: str
    impact: str
    mitigation: str
    status: Status

class PrivacyInvariant(BaseModel):
    id: str = Field(..., pattern=r"^PRIV-\d{2}$")
    description: str
    test_tool: Optional[str] = None
    test_method: Optional[str] = None

class ExitPhase(BaseModel):
    phase: str
    milestones: str
    asset_sale: str
    equity_round: str
    comps: Optional[str] = None

class AuditEntry(BaseModel):
    timestamp: str
    commit_sha: str
    reason: str
    adr_ref: Optional[str] = None
    actor: str = "Fatih Dinc"
    pipeline_url: Optional[HttpUrl] = None

class Masterplan(BaseModel):
    version: str = "1.0.0"
    generated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    author: str = "Fatih Dinc"
    organization: str = "datalabel.tech"
    repository: str = "https://gitlab.com/fatdinhero/cognitum"
    constitution: str = "constitution.md"
    glossary: str = "glossary.md"
    constitution_articles: List[ConstitutionArticle] = Field(default_factory=list)
    adrs: List[ADR] = Field(default_factory=list)
    modules: List[Module] = Field(default_factory=list)
    iso_25010: List[Iso25010Characteristic] = Field(default_factory=list)
    iso_23894_risks: List[RiskItem] = Field(default_factory=list)
    privacy_invariants: List[PrivacyInvariant] = Field(default_factory=list)
    exit_plan: List[ExitPhase] = Field(default_factory=list)
    audit_trail: List[AuditEntry] = Field(default_factory=list)
    class Config:
        extra = "forbid"
