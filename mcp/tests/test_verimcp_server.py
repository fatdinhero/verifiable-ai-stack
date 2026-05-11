"""Tests for the VeriMCP FastAPI facade."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient


APP_PATH = Path(__file__).resolve().parents[1] / "server" / "app.py"


def _load_app():
    spec = importlib.util.spec_from_file_location("verimcp_app", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


def test_health_endpoint():
    client = TestClient(_load_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_governance_claim_export_endpoint():
    client = TestClient(_load_app())

    response = client.post("/governance/claims", json={"limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_count"] == 3
    assert all("statement" in claim for claim in payload["claims"])


def test_governance_audit_endpoint_without_claim_payload():
    client = TestClient(_load_app())

    response = client.post(
        "/governance/audit",
        json={"limit": 5, "validators": ["baseline"], "include_claims": False},
    )

    assert response.status_code == 200
    report = response.json()["report"]
    assert report["report_schema"] == "verifiable-ai-stack/governance-audit/v2.4"
    assert report["quality_gate"]["passed"] is True
    assert report["claims"] == []


def test_compliance_endpoint_flags_eu_ai_act_risk_and_halal_review():
    client = TestClient(_load_app())

    response = client.post(
        "/compliance/check",
        json={
            "system_name": "DaySensOS",
            "system_description": "Privacy-first wearable AI coach",
            "domain": "wearable health",
            "processes_biometrics": False,
            "halal": {
                "protocol_name": "unknown-defi",
                "transaction_type": "spot purchase",
                "features": [],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["eu_ai_act"]["risk_level"] in {"minimal", "limited", "high", "prohibited"}
    assert payload["halal"]["status"] in {"halal", "haram", "needs_review"}


def test_compliance_endpoint_detects_haram_features():
    client = TestClient(_load_app())

    response = client.post(
        "/compliance/check",
        json={
            "halal": {
                "protocol_name": "lending",
                "transaction_type": "fixed_interest loan",
                "features": ["interest"],
            }
        },
    )

    assert response.status_code == 200
    halal = response.json()["halal"]
    assert halal["status"] == "haram"
    assert halal["violations"]
