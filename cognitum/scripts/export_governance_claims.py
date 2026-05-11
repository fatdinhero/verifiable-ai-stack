#!/usr/bin/env python3
"""Export and validate COGNITUM governance claims with AgentsProtocol.

This module is the canonical COGNITUM -> AgentsProtocol integration. It reads
`cognitum/governance/masterplan.yaml`, turns governance facts into deterministic
claims, validates them through one or more validator profiles, computes
AgentsProtocol `S_con`, `Psi`, and `check_acceptance`, and writes an audit
report under `docs/governance-audit/`.

Design principles:
- COGNITUM remains the governance Single Source of Truth.
- AgentsProtocol remains the semantic validation authority.
- Reports are deterministic, hash-addressable, and optionally signed.
- The default path is side-effect-light and never mutates the masterplan.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - only triggered in incomplete envs
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


COGNITUM_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COGNITUM_ROOT.parent
DEFAULT_MASTERPLAN = COGNITUM_ROOT / "governance" / "masterplan.yaml"
DEFAULT_AUDIT_DIR = REPO_ROOT / "docs" / "governance-audit"
AGENTSPROTOCOL_SRC = REPO_ROOT / "agentsprotocol" / "src"

REPORT_SCHEMA = "verifiable-ai-stack/governance-audit/v2"
REPORT_VERSION = "2.0.0"
CLAIM_SCHEMA = "verifiable-ai-stack/governance-claim/v1"
DEFAULT_VALIDATORS = ("baseline",)
DEFAULT_HMAC_ENV = "GOVERNANCE_AUDIT_HMAC_KEY"

if str(AGENTSPROTOCOL_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTSPROTOCOL_SRC))

from agentsprotocol import check_acceptance, compute_psi, compute_s_con  # noqa: E402


Claim = dict[str, Any]
ValidatorResult = dict[str, Any]


@dataclass(frozen=True)
class ValidatorProfile:
    """Built-in deterministic validator profile.

    External validators can be supplied with `--validator-results`. Built-ins
    provide CI-safe validation modes that use AgentsProtocol primitives without
    network calls or private data.
    """

    name: str
    description: str
    corpus_mode: str
    tau: float


BUILT_IN_VALIDATORS: dict[str, ValidatorProfile] = {
    "baseline": ValidatorProfile(
        name="baseline",
        description="Deterministic self-consistency validator for CI quality gates.",
        corpus_mode="self",
        tau=0.1,
    ),
    "kind-context": ValidatorProfile(
        name="kind-context",
        description="Compares each claim against claims of the same governance kind.",
        corpus_mode="same-kind",
        tau=0.1,
    ),
    "full-context": ValidatorProfile(
        name="full-context",
        description="Compares each claim against the complete exported governance corpus.",
        corpus_mode="full",
        tau=0.1,
    ),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_data(data: Any) -> str:
    return _sha256_text(_canonical_json(data))


def _load_masterplan(masterplan_path: Path) -> dict[str, Any]:
    with masterplan_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {masterplan_path}")
    return data


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _claim(
    *,
    kind: str,
    source_id: str,
    title: str,
    statement: str,
    metadata: Mapping[str, Any],
) -> Claim:
    original_claim = {
        "schema": CLAIM_SCHEMA,
        "kind": kind,
        "source": "cognitum/governance/masterplan.yaml",
        "source_id": source_id,
        "title": title,
        "statement": statement,
        "metadata": dict(metadata),
    }
    original_claim_sha256 = _sha256_data(original_claim)
    return {
        **original_claim,
        "id": original_claim_sha256,
        "original_claim_sha256": original_claim_sha256,
    }


def _constitution_claims(masterplan: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
    for item in _as_list(masterplan.get("constitution_articles")):
        article_id = str(item.get("id", "unknown"))
        title = item.get("title") or f"Article {article_id}"
        text = item.get("text", "")
        statement = f"COGNITUM constitution article {article_id} ({title}) states: {text}"
        claims.append(
            _claim(
                kind="constitution_article",
                source_id=article_id,
                title=title,
                statement=statement,
                metadata={"article_id": article_id},
            )
        )
    return claims


def _adr_claims(masterplan: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
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
        claims.append(
            _claim(
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
        )
    return claims


def _module_claims(masterplan: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
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
        links = module.get("links") or {}
        claims.append(
            _claim(
                kind="module",
                source_id=module_id,
                title=title,
                statement=statement,
                metadata={
                    "status": status,
                    "version": module.get("version"),
                    "layer": module.get("layer"),
                    "upstream": links.get("upstream", []),
                    "downstream": links.get("downstream", []),
                },
            )
        )
    return claims


def _risk_claims(masterplan: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
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
        claims.append(
            _claim(
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
        )
    return claims


def _privacy_claims(masterplan: dict[str, Any]) -> list[Claim]:
    claims: list[Claim] = []
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
        claims.append(
            _claim(
                kind="privacy_invariant",
                source_id=invariant_id,
                title=invariant_id,
                statement=statement,
                metadata={
                    "test_tool": test_tool,
                    "test_method": test_method,
                },
            )
        )
    return claims


def export_governance_claims(masterplan_path: Path = DEFAULT_MASTERPLAN) -> list[Claim]:
    """Export typed governance claims from the COGNITUM masterplan."""
    masterplan = _load_masterplan(masterplan_path)
    claims: list[Claim] = []
    claims.extend(_constitution_claims(masterplan))
    claims.extend(_adr_claims(masterplan))
    claims.extend(_module_claims(masterplan))
    claims.extend(_risk_claims(masterplan))
    claims.extend(_privacy_claims(masterplan))
    return claims


def _corpus_for_claim(
    claim: Claim,
    claims: Sequence[Claim],
    corpus_mode: str,
) -> list[str]:
    if corpus_mode == "self":
        return [claim["statement"]]
    if corpus_mode == "same-kind":
        corpus = [item["statement"] for item in claims if item["kind"] == claim["kind"]]
        return corpus or [claim["statement"]]
    if corpus_mode == "full":
        return [item["statement"] for item in claims]
    raise ValueError(f"Unsupported corpus mode: {corpus_mode}")


def _run_builtin_validator(
    profile: ValidatorProfile,
    claims: Sequence[Claim],
) -> ValidatorResult:
    scores: dict[str, float] = {}
    for claim in claims:
        corpus = _corpus_for_claim(claim, claims, profile.corpus_mode)
        scores[claim["id"]] = compute_s_con(claim["statement"], corpus, tau=profile.tau)
    return {
        "name": profile.name,
        "type": "built-in",
        "description": profile.description,
        "corpus_mode": profile.corpus_mode,
        "tau": profile.tau,
        "scores": scores,
    }


def _load_external_validator_results(path: Path, claims: Sequence[Claim]) -> list[ValidatorResult]:
    """Load external validator outputs from JSON.

    Expected shape:
    {
      "validators": [
        {
          "name": "validator-name",
          "scores": {"<claim-id>": 0.95}
        }
      ]
    }
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    validators = data.get("validators", data if isinstance(data, list) else [])
    if not isinstance(validators, list):
        raise ValueError("External validator results must contain a validators list")

    claim_ids = {claim["id"] for claim in claims}
    results: list[ValidatorResult] = []
    for entry in validators:
        if not isinstance(entry, dict):
            raise ValueError("Each external validator entry must be an object")
        name = entry.get("name")
        scores = entry.get("scores")
        if not name or not isinstance(scores, dict):
            raise ValueError("External validator entries require name and scores")
        missing = sorted(claim_ids - set(scores))
        if missing:
            raise ValueError(
                f"External validator {name!r} is missing {len(missing)} claim scores"
            )
        normalized = {claim_id: float(scores[claim_id]) for claim_id in claim_ids}
        for claim_id, score in normalized.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"External validator {name!r} score for {claim_id} is outside [0, 1]"
                )
        results.append(
            {
                "name": str(name),
                "type": "external",
                "description": entry.get("description", "External validator result"),
                "scores": normalized,
            }
        )
    return results


def _select_builtin_validators(names: Sequence[str]) -> list[ValidatorProfile]:
    profiles: list[ValidatorProfile] = []
    for name in names:
        if name not in BUILT_IN_VALIDATORS:
            available = ", ".join(sorted(BUILT_IN_VALIDATORS))
            raise ValueError(f"Unknown validator {name!r}. Available: {available}")
        profiles.append(BUILT_IN_VALIDATORS[name])
    return profiles


def _score_claims(
    claims: Sequence[Claim],
    validator_results: Sequence[ValidatorResult],
) -> list[dict[str, Any]]:
    scored_claims: list[dict[str, Any]] = []
    for claim in claims:
        scores = [
            float(result["scores"][claim["id"]])
            for result in validator_results
            if claim["id"] in result["scores"]
        ]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        scored_claims.append(
            {
                "id": claim["id"],
                "claim_schema": claim["schema"],
                "original_claim_sha256": claim["original_claim_sha256"],
                "kind": claim["kind"],
                "source": claim["source"],
                "source_id": claim["source_id"],
                "title": claim["title"],
                "statement": claim["statement"],
                "s_con": round(mean_score, 6),
                "validator_scores": {
                    result["name"]: round(float(result["scores"][claim["id"]]), 6)
                    for result in validator_results
                    if claim["id"] in result["scores"]
                },
                "metadata": claim["metadata"],
            }
        )
    return scored_claims


def _validator_error_vectors(
    claims: Sequence[Claim],
    validator_results: Sequence[ValidatorResult],
    reference_scores: Mapping[str, float],
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for result in validator_results:
        vectors.append(
            [
                abs(float(result["scores"][claim["id"]]) - reference_scores[claim["id"]])
                for claim in claims
            ]
        )
    return vectors


def _counts_by_kind(claims: Sequence[Claim]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for claim in claims:
        counts[claim["kind"]] = counts.get(claim["kind"], 0) + 1
    return counts


def _report_payload_hash(report_without_integrity: Mapping[str, Any]) -> str:
    return _sha256_data(report_without_integrity)


def _signature_block(report_hash: str, hmac_key_env: str) -> dict[str, Any]:
    key = os.getenv(hmac_key_env)
    if not key:
        return {
            "status": "unsigned",
            "algorithm": None,
            "key_id": hmac_key_env,
            "value": None,
            "reason": f"Environment variable {hmac_key_env} is not set",
        }
    signature = hmac.new(key.encode("utf-8"), report_hash.encode("utf-8"), hashlib.sha256)
    return {
        "status": "signed",
        "algorithm": "HMAC-SHA256",
        "key_id": hmac_key_env,
        "value": signature.hexdigest(),
    }


def validate_governance_claims(
    claims: Sequence[Claim],
    *,
    validator_names: Sequence[str] = DEFAULT_VALIDATORS,
    validator_results_path: Path | None = None,
    theta_min: float = 0.6,
    psi_min: float = 0.7,
    generated_at: datetime | None = None,
    masterplan_path: Path = DEFAULT_MASTERPLAN,
    hmac_key_env: str = DEFAULT_HMAC_ENV,
) -> dict[str, Any]:
    """Validate exported governance claims and return an audit report."""
    if not claims:
        raise ValueError("No governance claims were exported")

    generated_at = generated_at or _utc_now()
    builtin_results = [
        _run_builtin_validator(profile, claims)
        for profile in _select_builtin_validators(validator_names)
    ]
    external_results = (
        _load_external_validator_results(validator_results_path, claims)
        if validator_results_path
        else []
    )
    validator_results = [*builtin_results, *external_results]
    if not validator_results:
        raise ValueError("At least one validator is required")

    reference_scores = {
        claim["id"]: float(validator_results[0]["scores"][claim["id"]])
        for claim in claims
    }
    scored_claims = _score_claims(claims, validator_results)
    aggregate_scores = [float(claim["s_con"]) for claim in scored_claims]
    error_vectors = _validator_error_vectors(claims, validator_results, reference_scores)
    psi = compute_psi(error_vectors)
    accepted = check_acceptance(aggregate_scores, psi, theta_min=theta_min, psi_min=psi_min)
    mean_s_con = sum(aggregate_scores) / len(aggregate_scores) if aggregate_scores else 0.0

    report_without_integrity: dict[str, Any] = {
        "report_schema": REPORT_SCHEMA,
        "report_version": REPORT_VERSION,
        "generated_at": generated_at.isoformat(),
        "generated_date": generated_at.date().isoformat(),
        "source": "cognitum/governance/masterplan.yaml",
        "source_sha256": _file_sha256(masterplan_path),
        "validator": "agentsprotocol",
        "parameters": {
            "theta_min": theta_min,
            "psi_min": psi_min,
            "validators": list(validator_names),
            "external_validator_results": str(validator_results_path)
            if validator_results_path
            else None,
        },
        "quality_model": {
            "vdi": "VDI 2221/2225 systematic decision and evaluation traceability",
            "iso_25010": [
                "functional suitability",
                "reliability",
                "maintainability",
                "security",
            ],
            "auditability": [
                "stable claim identifiers",
                "original claim SHA-256 hashes",
                "report payload SHA-256",
                "optional HMAC-SHA256 signature",
            ],
        },
        "summary": {
            "claim_count": len(scored_claims),
            "counts_by_kind": _counts_by_kind(claims),
            "validator_count": len(validator_results),
            "mean_s_con": round(mean_s_con, 6),
            "psi": round(psi, 6),
            "accepted": accepted,
        },
        "validators": [
            {
                "name": result["name"],
                "type": result["type"],
                "description": result.get("description"),
                "corpus_mode": result.get("corpus_mode"),
                "tau": result.get("tau"),
            }
            for result in validator_results
        ],
        "claims": scored_claims,
    }
    report_hash = _report_payload_hash(report_without_integrity)
    return {
        **report_without_integrity,
        "integrity": {
            "report_payload_sha256": report_hash,
            "signature": _signature_block(report_hash, hmac_key_env),
        },
    }


def audit_report_filename(generated_at: datetime) -> str:
    """Return the versioned report filename required by the audit contract."""
    return f"{generated_at.strftime('%Y-%m-%d_%H-%M')}.json"


def write_audit_report(report: dict[str, Any], audit_dir: Path = DEFAULT_AUDIT_DIR) -> Path:
    """Write a minute-versioned audit report and update latest.json."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.fromisoformat(report["generated_at"])
    report_path = audit_dir / audit_report_filename(generated_at)
    latest_path = audit_dir / "latest.json"
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    report_path.write_text(rendered, encoding="utf-8")
    latest_path.write_text(rendered, encoding="utf-8")
    return report_path


def _parse_validator_names(raw: str) -> tuple[str, ...]:
    names = tuple(name.strip() for name in raw.split(",") if name.strip())
    return names or DEFAULT_VALIDATORS


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masterplan", type=Path, default=DEFAULT_MASTERPLAN)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Limit exported claims")
    parser.add_argument("--theta-min", type=float, default=0.6)
    parser.add_argument("--psi-min", type=float, default=0.7)
    parser.add_argument(
        "--validators",
        default=",".join(DEFAULT_VALIDATORS),
        help=(
            "Comma-separated built-in validators. Available: "
            + ", ".join(sorted(BUILT_IN_VALIDATORS))
        ),
    )
    parser.add_argument(
        "--validator-results",
        type=Path,
        default=None,
        help="Optional JSON file with external validator scores.",
    )
    parser.add_argument("--hmac-key-env", default=DEFAULT_HMAC_ENV)
    parser.add_argument("--stdout", action="store_true", help="Print report instead of writing")
    parser.add_argument(
        "--fail-on-reject",
        action="store_true",
        help="Exit with code 1 when the governance quality gate is rejected.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    claims = export_governance_claims(args.masterplan)
    if args.limit > 0:
        claims = claims[: args.limit]

    try:
        report = validate_governance_claims(
            claims,
            validator_names=_parse_validator_names(args.validators),
            validator_results_path=args.validator_results,
            theta_min=args.theta_min,
            psi_min=args.psi_min,
            masterplan_path=args.masterplan,
            hmac_key_env=args.hmac_key_env,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Governance audit failed before validation: {exc}") from exc

    if args.stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        report_path = write_audit_report(report, args.audit_dir)
        print(f"Wrote governance audit report: {report_path}")

    if args.fail_on_reject and not report["summary"]["accepted"]:
        raise SystemExit(
            "Governance audit quality gate rejected: "
            f"mean_s_con={report['summary']['mean_s_con']} "
            f"psi={report['summary']['psi']}"
        )


if __name__ == "__main__":
    main()
