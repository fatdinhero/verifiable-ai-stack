"""
incident_log.py — EU AI Act Art.12/19 Incident Logging Module
PoISV / AgentsProtocol — Fatih Dinc, 2026
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Enums & constants
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


EU_AI_ACT_TAGS = {
    "Art.12": "Record-keeping and logging requirements",
    "Art.19": "Automatically generated logs",
    "Art.9":  "Risk management system",
    "Art.13": "Transparency and provision of information to users",
    "Art.62": "Reporting of serious incidents",
}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    """Input payload for creating / checking an incident."""

    claim_id: str = Field(..., description="Unique identifier of the semantic claim")
    block_id: str = Field(..., description="DAG block hash where the claim was anchored")
    psi: float = Field(..., ge=0.0, le=1.0, description="Ψ entanglement measure")
    bell_S: float = Field(..., description="CHSH Bell-S value (|Bell_S| ≤ 2√2)")
    bell_delta: float = Field(..., description="|Bell_S| − 2√2  (negative ⟹ no violation)")
    scon: float = Field(..., ge=0.0, le=1.0, description="Semantic consensus score S_con")
    severity: Optional[Severity] = Field(
        None,
        description="Override severity; auto-computed from bell_delta / scon if omitted",
    )
    eu_ai_act_tags: list[str] = Field(
        default_factory=lambda: ["Art.12", "Art.19"],
        description="Applicable EU AI Act article tags",
    )

    @model_validator(mode="after")
    def validate_tags(self) -> "IncidentCreate":
        unknown = [t for t in self.eu_ai_act_tags if t not in EU_AI_ACT_TAGS]
        if unknown:
            raise ValueError(f"Unknown EU AI Act tags: {unknown}")
        return self


class IncidentRecord(BaseModel):
    """Full incident record stored in memory and returned via API."""

    incident_id: str = Field(..., description="SHA-256 fingerprint of the incident payload")
    claim_id: str
    block_id: str
    psi: float
    bell_S: float
    bell_delta: float
    scon: float
    severity: Severity
    eu_ai_act_tags: list[str]
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")


# ---------------------------------------------------------------------------
# In-memory store (replace with DB in production)
# ---------------------------------------------------------------------------

_incident_store: dict[str, IncidentRecord] = {}


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def _compute_severity(bell_delta: float, scon: float) -> Severity:
    """Auto-derive severity from physical indicators."""
    if bell_delta > 0.1 or scon < 0.3:
        return Severity.HIGH
    if bell_delta > 0.0 or scon < 0.6:
        return Severity.MEDIUM
    return Severity.LOW


def _make_incident_id(payload: dict) -> str:
    """Deterministic SHA-256 fingerprint of the incident payload."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_incident(data: IncidentCreate) -> IncidentRecord:
    """Create an IncidentRecord from an IncidentCreate payload."""
    severity = data.severity or _compute_severity(data.bell_delta, data.scon)
    ts = datetime.now(timezone.utc).isoformat()

    payload = {
        "claim_id": data.claim_id,
        "block_id": data.block_id,
        "psi": data.psi,
        "bell_S": data.bell_S,
        "bell_delta": data.bell_delta,
        "scon": data.scon,
        "severity": severity.value,
        "eu_ai_act_tags": sorted(data.eu_ai_act_tags),
        "timestamp": ts,
    }
    incident_id = _make_incident_id(payload)
    record = IncidentRecord(incident_id=incident_id, **payload)
    _incident_store[incident_id] = record
    return record


# ---------------------------------------------------------------------------
# FastAPI app & routes
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PoISV Incident Log",
    description=(
        "EU AI Act Art.12/19 compliant incident logging for the PoISV / "
        "AgentsProtocol semantic validation pipeline."
    ),
    version="1.0.0",
)


@app.post(
    "/incidents/check",
    response_model=IncidentRecord,
    summary="Submit and log a validation incident",
    tags=["Incidents"],
)
def check_incident(data: IncidentCreate) -> IncidentRecord:
    """
    Receive a validation event, compute severity (unless overridden),
    generate a deterministic SHA-256 incident_id, persist, and return
    the full IncidentRecord.

    Complies with:
    - **Art.12** — automatic logging with tamper-evident identifiers
    - **Art.19** — auto-generated logs retained per incident
    """
    return create_incident(data)


@app.get(
    "/incidents/",
    response_model=list[IncidentRecord],
    summary="List all logged incidents",
    tags=["Incidents"],
)
def list_incidents(
    severity: Optional[Severity] = Query(None, description="Filter by severity level"),
    tag: Optional[str] = Query(None, description="Filter by EU AI Act tag, e.g. Art.12"),
) -> list[IncidentRecord]:
    """Return all incidents, optionally filtered by severity or EU AI Act tag."""
    records = list(_incident_store.values())
    if severity:
        records = [r for r in records if r.severity == severity]
    if tag:
        records = [r for r in records if tag in r.eu_ai_act_tags]
    return sorted(records, key=lambda r: r.timestamp, reverse=True)


@app.get(
    "/incidents/export/eu-ai-act",
    summary="Export incidents in EU AI Act structured format",
    tags=["Export"],
)
def export_eu_ai_act(
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
) -> dict:
    """
    Export all incidents in a structured JSON format suitable for EU AI Act
    regulatory reporting (Art.62 serious incident notifications).
    """
    records = list(_incident_store.values())
    if severity:
        records = [r for r in records if r.severity == severity]

    return {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "regulation": "EU AI Act",
        "applicable_articles": list(EU_AI_ACT_TAGS.keys()),
        "total_incidents": len(records),
        "incidents": [r.model_dump() for r in sorted(records, key=lambda r: r.timestamp)],
    }
