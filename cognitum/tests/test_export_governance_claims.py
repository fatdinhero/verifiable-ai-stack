import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_governance_claims.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("export_governance_claims", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_exports_expected_governance_claim_kinds():
    module = _load_module()

    claims = module.export_governance_claims()
    kinds = {claim["kind"] for claim in claims}

    assert "architecture_decision" in kinds
    assert "module" in kinds
    assert "risk" in kinds
    assert "privacy_invariant" in kinds
    assert all(claim["id"] and claim["statement"] for claim in claims)


def test_validates_claims_with_agentsprotocol_primitives():
    module = _load_module()

    claims = module.export_governance_claims()[:6]
    report = module.validate_governance_claims(claims)

    assert report["validator"] == "agentsprotocol"
    assert report["summary"]["claim_count"] == 6
    assert report["summary"]["accepted"] is True
    assert report["summary"]["mean_s_con"] == 1.0
    assert report["summary"]["psi"] == 1.0


def test_writes_latest_audit_report(tmp_path):
    module = _load_module()

    claims = module.export_governance_claims()[:3]
    report = module.validate_governance_claims(claims)
    report_path = module.write_audit_report(report, tmp_path)
    latest_path = tmp_path / "latest.json"

    assert report_path.exists()
    assert latest_path.exists()
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["summary"]["claim_count"] == 3
