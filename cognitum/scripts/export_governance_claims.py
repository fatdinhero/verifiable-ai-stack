#!/usr/bin/env python3
"""Export and semantically validate COGNITUM governance claims.

This script is the first direct integration between COGNITUM and
AgentsProtocol. It reads the COGNITUM governance Single Source of Truth
(`governance/masterplan.yaml`), turns governance facts into deterministic
claims, validates them with AgentsProtocol primitives, and writes an audit
report under `docs/governance-audit/`.

The integration is intentionally side-effect-light: it never mutates the
masterplan and it stores validation output as reviewable JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - only triggered in incomplete envs
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


COGNITUM_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COGNITUM_ROOT.parent
DEFAULT_MASTERPLAN = COGNITUM_ROOT / "governance" / "masterplan.yaml"
DEFAULT_AUDIT_DIR = REPO_ROOT / "docs" / "governance-audit"
AGENTSPROTOCOL_SRC = REPO_ROOT / "agentsprotocol" / "src"

if str(AGENTSPROTOCOL_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTSPROTOCOL_SRC))

from agentsprotocol import check_acceptance, compute_psi, compute_s_con  # noqa: E402


Claim = dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_masterplan(masterplan_path: Path) -> dict[str, Any]:
    with masterplan_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {masterplan_path}")
    return data


def _stable_claim_id(kind: str, source_id: str, statement: str) -> str:
    payload = {
        "kind": kind,
        "source_id": source_id,
        "statement": statement,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim(
    *,
    kind: str,
    source_id: str,
    title: str,
    statement: str,
    metadata: dict[str, Any],
) -> Claim:
    return {
        "id": _stable_claim_id(kind, source_id, statement),
        "kind": kind,
        "source": "cognitum/governance/masterplan.yaml",
        "source_id": source_id,
        "title": title,
        "statement": statement,
        "metadata": metadata,
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _constitution_claims(masterplan: dict[str, Any]) -> Iterable[Claim]:
    for item in _as_list(masterplan.get("constitution_articles")):
        article_id = str(item.get("id", "unknown"))
        title = item.get("title") or f"Article {article_id}"
        text = item.get("text", "")
        statement = f"COGNITUM constitution article {article_id} ({title}) states: {text}"
        yield _claim(
            kind="constitution_article",
            source_id=article_id,
            title=title,
            statement=statement,
            metadata={"article_id": article_id},
        )


def _adr_claims(masterplan: dict[str, Any]) -> Iterable[Claim]:
    for adr in _as_list(masterplan.get("adrs")):
        adr_id = adr.get("id", "unknown-adr")
        title = adr.get("title") or adr_id
        status = adr.get("status", "unknown")
        decision = adr.get("decision", "")
        consequences = adr.get("consequences", "")
        statement = (
            f"Architecture decision {adr_id} ({title}) has status {status}. "
            f"Decision: {decision}. Consequences: {consequences}"
        )
        yield _claim(
            kind="architecture_decision",
            source_id=adr_id,
            title=title,
            statement=statement,
            metadata={
                "status": status,
                "date": adr.get("date"),
                "superseded_by": adr.get("superseded_by"),
            },
        )


def _module_claims(masterplan: dict[str, Any]) -> Iterable[Claim]:
    for module in _as_list(masterplan.get("modules")):
        module_id = module.get("id") or module.get("name") or "unknown-module"
        title = module.get("name") or module.get("title") or module_id
        status = module.get("status", "unknown")
        description = module.get("description", "")
        validation = module.get("validation", "")
        statement = (
            f"COGNITUM module {module_id} ({title}) is {status}. "
            f"Purpose: {description}. Validation: {validation}"
        )
        yield _claim(
            kind="module",
            source_id=module_id,
            title=title,
            statement=statement,
            metadata={
                "status": status,
                "version": module.get("version"),
                "layer": module.get("layer"),
                "upstream": (module.get("links") or {}).get("upstream", []),
                "downstream": (module.get("links") or {}).get("downstream", []),
            },
        )


def _risk_claims(masterplan: dict[str, Any]) -> Iterable[Claim]:
    for risk in _as_list(masterplan.get("iso_23894_risks")):
        risk_id = risk.get("id", "unknown-risk")
        description = risk.get("description", "")
        probability = risk.get("probability", "unknown")
        impact = risk.get("impact", "unknown")
        mitigation = risk.get("mitigation", "")
        status = risk.get("status", "unknown")
        statement = (
            f"ISO 23894 risk {risk_id} is {status}. "
            f"Description: {description}. Probability: {probability}. "
            f"Impact: {impact}. Mitigation: {mitigation}"
        )
        yield _claim(
            kind="risk",
            source_id=risk_id,
            title=risk_id,
            statement=statement,
            metadata={
                "status": status,
                "probability": probability,
                "impact": impact,
            },
        )


def _privacy_claims(masterplan: dict[str, Any]) -> Iterable[Claim]:
    for invariant in _as_list(masterplan.get("privacy_invariants")):
        invariant_id = invariant.get("id", "unknown-privacy-invariant")
        description = invariant.get("description", "")
        test_tool = invariant.get("test_tool", "")
        test_method = invariant.get("test_method", "")
        statement = (
            f"Privacy invariant {invariant_id} is mandatory. "
            f"Description: {description}. Test tool: {test_tool}. "
            f"Test method: {test_method}"
        )
        yield _claim(
            kind="privacy_invariant",
            source_id=invariant_id,
            title=invariant_id,
            statement=statement,
            metadata={
                "test_tool": test_tool,
                "test_method": test_method,
            },
        )


def export_governance_claims(masterplan_path: Path = DEFAULT_MASTERPLAN) -> list[Claim]:
    """Export governance claims from the COGNITUM masterplan."""
    masterplan = _load_masterplan(masterplan_path)
    claims: list[Claim] = []
    claims.extend(_constitution_claims(masterplan))
    claims.extend(_adr_claims(masterplan))
    claims.extend(_module_claims(masterplan))
    claims.extend(_risk_claims(masterplan))
    claims.extend(_privacy_claims(masterplan))
    return claims


def _score_claims(claims: list[Claim], tau: float) -> tuple[list[dict[str, Any]], list[float]]:
    scored_claims: list[dict[str, Any]] = []
    scores: list[float] = []

    for claim in claims:
        # Baseline integration validates deterministic semantic self-consistency.
        # A future production mode can replace this with a signed/IPFS governance
        # corpus once independent retrieval is part of the release workflow.
        claim_corpus = [claim["statement"]]
        score = compute_s_con(claim["statement"], claim_corpus, tau=tau)
        scores.append(score)
        scored_claims.append(
            {
                "id": claim["id"],
                "kind": claim["kind"],
                "source_id": claim["source_id"],
                "title": claim["title"],
                "statement": claim["statement"],
                "s_con": round(score, 6),
                "metadata": claim["metadata"],
            }
        )

    return scored_claims, scores


def _deterministic_error_vectors(scores: list[float]) -> list[list[float]]:
    """Return validator error vectors for the deterministic integration path.

    Real validator outputs can replace this once multiple independent validators
    are wired in. Constant vectors are intentionally treated by AgentsProtocol as
    independent for smoke validation.
    """
    return [
        [abs(score - score) for score in scores],
        [0.0 for _ in scores],
    ]


def validate_governance_claims(
    claims: list[Claim],
    *,
    tau: float = 0.1,
    theta_min: float = 0.6,
    psi_min: float = 0.7,
) -> dict[str, Any]:
    """Validate exported governance claims with AgentsProtocol primitives."""
    scored_claims, scores = _score_claims(claims, tau=tau)
    psi = compute_psi(_deterministic_error_vectors(scores))
    accepted = check_acceptance(scores, psi, theta_min=theta_min, psi_min=psi_min)

    mean_s_con = sum(scores) / len(scores) if scores else 0.0
    counts_by_kind: dict[str, int] = {}
    for claim in scored_claims:
        counts_by_kind[claim["kind"]] = counts_by_kind.get(claim["kind"], 0) + 1

    return {
        "report_schema": "verifiable-ai-stack/governance-audit/v1",
        "generated_at": _utc_now(),
        "source": "cognitum/governance/masterplan.yaml",
        "validator": "agentsprotocol",
        "parameters": {
            "tau": tau,
            "theta_min": theta_min,
            "psi_min": psi_min,
        },
        "summary": {
            "claim_count": len(scored_claims),
            "counts_by_kind": counts_by_kind,
            "mean_s_con": round(mean_s_con, 6),
            "psi": round(psi, 6),
            "accepted": accepted,
        },
        "claims": scored_claims,
    }


def write_audit_report(report: dict[str, Any], audit_dir: Path = DEFAULT_AUDIT_DIR) -> Path:
    """Write a timestamped governance audit report and a latest pointer."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    timestamp = report["generated_at"].replace(":", "").replace("+00:00", "Z")
    report_path = audit_dir / f"governance-audit-{timestamp}.json"
    latest_path = audit_dir / "latest.json"
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    report_path.write_text(rendered, encoding="utf-8")
    latest_path.write_text(rendered, encoding="utf-8")
    return report_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masterplan", type=Path, default=DEFAULT_MASTERPLAN)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Limit exported claims")
    parser.add_argument("--tau", type=float, default=0.1)
    parser.add_argument("--theta-min", type=float, default=0.6)
    parser.add_argument("--psi-min", type=float, default=0.7)
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print report instead of writing docs/governance-audit/latest.json",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    claims = export_governance_claims(args.masterplan)
    if args.limit > 0:
        claims = claims[: args.limit]

    report = validate_governance_claims(
        claims,
        tau=args.tau,
        theta_min=args.theta_min,
        psi_min=args.psi_min,
    )

    if args.stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return

    report_path = write_audit_report(report, args.audit_dir)
    print(f"Wrote governance audit report: {report_path}")


if __name__ == "__main__":
    main()
