"""
incident_routes.py — APIRouter for EU AI Act incident endpoints
PoISV / AgentsProtocol — Fatih Dinc, 2026

Mount this router into an existing FastAPI app:

    from poisv.incident_routes import router as incident_router
    app.include_router(incident_router, prefix="/v1")
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .incident_log import (
    IncidentCreate,
    IncidentRecord,
    Severity,
    _incident_store,
    create_incident,
)

router = APIRouter(
    prefix="/incidents",
    tags=["EU AI Act — Incidents"],
)


# ---------------------------------------------------------------------------
# POST /incidents/check
# ---------------------------------------------------------------------------

@router.post(
    "/check",
    response_model=IncidentRecord,
    summary="Submit a validation event and create an incident record",
    description=(
        "Accepts a PoISV validation event, derives severity from Ψ / Bell_S / S_con "
        "metrics (unless explicitly overridden), generates a deterministic SHA-256 "
        "`incident_id`, persists the record, and returns it.\n\n"
        "**EU AI Act compliance**: Art.12 (automatic logging) · Art.19 (auto-generated logs)"
    ),
)
def post_check(data: IncidentCreate) -> IncidentRecord:
    return create_incident(data)


# ---------------------------------------------------------------------------
# GET /incidents/
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[IncidentRecord],
    summary="List all logged incidents",
    description="Return all persisted incident records, newest first. Supports filtering.",
)
def get_incidents(
    severity: Optional[Severity] = Query(None, description="Filter by severity (LOW/MEDIUM/HIGH)"),
    tag: Optional[str] = Query(None, description="Filter by EU AI Act tag, e.g. Art.12"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> list[IncidentRecord]:
    records = list(_incident_store.values())
    if severity:
        records = [r for r in records if r.severity == severity]
    if tag:
        records = [r for r in records if tag in r.eu_ai_act_tags]
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return records[offset : offset + limit]


# ---------------------------------------------------------------------------
# GET /incidents/{incident_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{incident_id}",
    response_model=IncidentRecord,
    summary="Retrieve a single incident by its SHA-256 ID",
)
def get_incident(incident_id: str) -> IncidentRecord:
    record = _incident_store.get(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return record


# ---------------------------------------------------------------------------
# GET /incidents/export/eu-ai-act
# ---------------------------------------------------------------------------

@router.get(
    "/export/eu-ai-act",
    summary="Export incidents for EU AI Act regulatory reporting",
    description=(
        "Returns a structured JSON export of all incidents suitable for "
        "Art.62 serious incident notifications and supervisory authority submissions."
    ),
)
def export_eu_ai_act(
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
) -> dict:
    from datetime import datetime, timezone
    from .incident_log import EU_AI_ACT_TAGS

    records = list(_incident_store.values())
    if severity:
        records = [r for r in records if r.severity == severity]
    records.sort(key=lambda r: r.timestamp)

    return {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "regulation": "EU AI Act",
        "applicable_articles": list(EU_AI_ACT_TAGS.keys()),
        "article_descriptions": EU_AI_ACT_TAGS,
        "total_incidents": len(records),
        "severity_breakdown": {
            s.value: sum(1 for r in records if r.severity == s)
            for s in Severity
        },
        "incidents": [r.model_dump() for r in records],
    }
