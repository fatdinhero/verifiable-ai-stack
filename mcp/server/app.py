"""VeriMCP FastAPI server.

VeriMCP composes existing monorepo capabilities into a small HTTP API:

- COGNITUM governance claim export
- AgentsProtocol semantic validation through the governance-audit engine
- basic EU AI Act and Halal compliance checks

The server is intentionally a facade. It does not duplicate governance or
protocol logic; it calls the canonical implementation in
`cognitum/scripts/export_governance_claims.py` and compliance modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
COGNITUM_SCRIPTS = REPO_ROOT / "cognitum" / "scripts"
EU_AI_ACT_ROOT = REPO_ROOT / "compliance" / "eu-ai-act"

for path in (COGNITUM_SCRIPTS, EU_AI_ACT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_governance_claims import (  # noqa: E402
    DEFAULT_AUDIT_DIR,
    DEFAULT_HMAC_ENV,
    DEFAULT_MASTERPLAN,
    DEFAULT_VALIDATORS,
    export_governance_claims,
    validate_governance_claims,
    write_audit_report,
)
from veriethiccore.eu_ai_act_rules import generate_full_compliance_report  # noqa: E402


logger = logging.getLogger("verimcp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class GovernanceClaimsRequest(BaseModel):
    """Request for exporting governance claims."""

    limit: int = Field(default=0, ge=0, description="Optional number of claims to return")


class GovernanceAuditRequest(BaseModel):
    """Request for validating governance claims and optionally writing an audit report."""

    limit: int = Field(default=0, ge=0)
    validators: list[str] = Field(default_factory=lambda: list(DEFAULT_VALIDATORS))
    validator_api: list[str] = Field(default_factory=list)
    theta_min: float = Field(default=0.6, ge=0.0, le=1.0)
    psi_min: float = Field(default=0.7, ge=0.0, le=1.0)
    require_signature: bool = False
    hmac_key_env: str = DEFAULT_HMAC_ENV
    write_report: bool = False
    include_claims: bool = True


class HalalCheckRequest(BaseModel):
    """Basic halal screening request."""

    protocol_name: str = ""
    transaction_type: str = ""
    features: list[str] = Field(default_factory=list)


class ComplianceCheckRequest(BaseModel):
    """Combined compliance request for EU AI Act and halal screening."""

    system_name: str = "VeriMCP System"
    system_description: str = "Privacy-first wearable AI governance and validation system"
    domain: str = "wearable AI"
    processes_biometrics: bool = False
    is_safety_component: bool = False
    discloses_ai_nature: bool = True
    discloses_emotion_recognition: bool = False
    labels_synthetic_content: bool = True
    uses_emotion_recognition: bool = False
    generates_synthetic_content: bool = False
    completed_hleg_criteria: list[str] = Field(default_factory=list)
    halal: HalalCheckRequest = Field(default_factory=HalalCheckRequest)


def _limited_claims(limit: int) -> list[dict[str, Any]]:
    claims = export_governance_claims(DEFAULT_MASTERPLAN)
    return claims[:limit] if limit > 0 else claims


def _screen_halal(request: HalalCheckRequest) -> dict[str, Any]:
    """Run a deterministic baseline halal screen.

    This is intentionally conservative and mirrors the categories used by
    zkHalal/COS. A future adapter can call `compliance/zkhalal-mcp` directly.
    """

    text = " ".join([request.protocol_name, request.transaction_type, *request.features]).lower()
    prohibited = {
        "riba": ["interest", "lending_with_interest", "fixed_interest", "usury"],
        "gharar": ["options", "futures", "short_selling", "excessive_leverage"],
        "maysir": ["gambling", "lottery", "zero_sum_betting", "casino"],
    }
    violations = []
    for category, triggers in prohibited.items():
        for trigger in triggers:
            if trigger in text:
                violations.append(
                    {
                        "category": category,
                        "trigger": trigger,
                        "severity": "critical" if category in {"riba", "maysir"} else "high",
                    }
                )

    status: Literal["halal", "haram", "needs_review"] = "halal"
    if violations:
        status = "haram"
    elif request.protocol_name or request.transaction_type or request.features:
        status = "needs_review"

    return {
        "domain": "halal",
        "status": status,
        "halal": status == "halal",
        "violations": violations,
        "human_review_required": status != "halal",
        "standard": "AAOIFI/DJIM-inspired baseline screen",
    }


def create_app() -> FastAPI:
    """Create and configure the VeriMCP FastAPI application."""

    app = FastAPI(
        title="VeriMCP",
        version="0.1.0",
        description=(
            "Governance, semantic validation, and compliance facade for "
            "verifiable-ai-stack."
        ),
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "service": "verimcp", "version": app.version}

    @app.post("/governance/claims")
    def governance_claims(request: GovernanceClaimsRequest) -> dict[str, Any]:
        try:
            claims = _limited_claims(request.limit)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception("Failed to export governance claims")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"claim_count": len(claims), "claims": claims}

    @app.post("/governance/audit")
    def governance_audit(request: GovernanceAuditRequest) -> dict[str, Any]:
        try:
            claims = _limited_claims(request.limit)
            report = validate_governance_claims(
                claims,
                validator_names=tuple(request.validators),
                validator_result_apis=tuple(request.validator_api),
                theta_min=request.theta_min,
                psi_min=request.psi_min,
                require_signature=request.require_signature,
                hmac_key_env=request.hmac_key_env,
            )
            report_path = None
            if request.write_report:
                report_path = str(write_audit_report(report, DEFAULT_AUDIT_DIR))
            if not request.include_claims:
                report = {**report, "claims": []}
            return {"report": report, "report_path": report_path}
        except ValueError as exc:
            logger.warning("Governance audit rejected request: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception("Failed to run governance audit")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/compliance/check")
    def compliance_check(request: ComplianceCheckRequest) -> dict[str, Any]:
        try:
            eu_report = generate_full_compliance_report(
                request.system_name,
                {
                    "system_description": request.system_description,
                    "domain": request.domain,
                    "processes_biometrics": request.processes_biometrics,
                    "is_safety_component": request.is_safety_component,
                    "discloses_ai_nature": request.discloses_ai_nature,
                    "discloses_emotion_recognition": request.discloses_emotion_recognition,
                    "labels_synthetic_content": request.labels_synthetic_content,
                    "uses_emotion_recognition": request.uses_emotion_recognition,
                    "generates_synthetic_content": request.generates_synthetic_content,
                    "completed_hleg_criteria": request.completed_hleg_criteria,
                },
            )
            halal_report = _screen_halal(request.halal)
            return {
                "overall_status": "pass"
                if eu_report["overall_compliant"] and halal_report["status"] == "halal"
                else "needs_review",
                "eu_ai_act": eu_report,
                "halal": halal_report,
            }
        except Exception as exc:  # pragma: no cover - defensive API boundary
            logger.exception("Failed to run compliance check")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()

