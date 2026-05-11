import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_governance_claims.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("export_governance_claims", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exports_expected_governance_claim_kinds():
    module = _load_module()

    claims = module.export_governance_claims()
    kinds = {claim["kind"] for claim in claims}

    assert "constitution_article" in kinds
    assert "architecture_decision" in kinds
    assert "module" in kinds
    assert "risk" in kinds
    assert "privacy_invariant" in kinds
    assert all(claim["id"] and claim["statement"] for claim in claims)
    assert all(claim["original_claim_sha256"] == claim["id"] for claim in claims)


def test_validates_claims_with_agentsprotocol_primitives():
    module = _load_module()

    claims = module.export_governance_claims()[:6]
    report = module.validate_governance_claims(claims)

    assert report["validator"] == "agentsprotocol"
    assert report["report_version"] == "2.0.0"
    assert report["summary"]["claim_count"] == 6
    assert report["summary"]["accepted"] is True
    assert report["summary"]["mean_s_con"] == 1.0
    assert report["summary"]["psi"] == 1.0
    assert report["integrity"]["report_payload_sha256"]
    assert report["integrity"]["signature"]["status"] == "unsigned"


def test_validates_with_multiple_builtin_validators():
    module = _load_module()

    claims = module.export_governance_claims()[:6]
    report = module.validate_governance_claims(
        claims,
        validator_names=("baseline", "kind-context"),
    )

    assert report["summary"]["validator_count"] == 2
    assert {validator["name"] for validator in report["validators"]} == {
        "baseline",
        "kind-context",
    }
    assert 0.0 <= report["summary"]["psi"] <= 1.0


def test_report_can_be_hmac_signed(monkeypatch):
    module = _load_module()
    monkeypatch.setenv("GOVERNANCE_AUDIT_HMAC_KEY", "test-secret")

    claims = module.export_governance_claims()[:2]
    report = module.validate_governance_claims(claims)

    signature = report["integrity"]["signature"]
    assert signature["status"] == "signed"
    assert signature["algorithm"] == "HMAC-SHA256"
    assert len(signature["value"]) == 64


def test_accepts_external_validator_results(tmp_path):
    module = _load_module()

    claims = module.export_governance_claims()[:4]
    external_path = tmp_path / "validators.json"
    external_path.write_text(
        json.dumps(
            {
                "validators": [
                    {
                        "name": "independent-validator-a",
                        "scores": {claim["id"]: 0.98 for claim in claims},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = module.validate_governance_claims(
        claims,
        validator_results_path=external_path,
    )

    assert report["summary"]["validator_count"] == 2
    assert report["summary"]["accepted"] is True
    assert {validator["type"] for validator in report["validators"]} == {
        "built-in",
        "external",
    }


def test_writes_latest_audit_report(tmp_path):
    module = _load_module()

    claims = module.export_governance_claims()[:3]
    report = module.validate_governance_claims(claims)
    report_path = module.write_audit_report(report, tmp_path)
    latest_path = tmp_path / "latest.json"

    assert report_path.exists()
    assert report_path.name.endswith(".json")
    assert report_path.name != "latest.json"
    assert latest_path.exists()
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["summary"]["claim_count"] == 3
