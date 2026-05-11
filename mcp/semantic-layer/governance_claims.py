#!/usr/bin/env python3
"""Export COGNITUM governance entries as deterministic bridge claims.

The bridge claim format is deliberately smaller than a signed AgentsProtocol
claim. It gives the monorepo a stable seam between the governance SSoT and the
semantic validation layer without mutating `masterplan.yaml`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only in incomplete envs
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTERPLAN = REPO_ROOT / "cognitum" / "governance" / "masterplan.yaml"


def _stable_id(kind: str, statement: str, metadata: dict[str, Any]) -> str:
    payload = {
        "kind": kind,
        "statement": statement,
        "metadata": metadata,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim(kind: str, statement: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _stable_id(kind, statement, metadata),
        "source": "cognitum/governance/masterplan.yaml",
        "kind": kind,
        "statement": statement,
        "metadata": metadata,
    }


def _module_claims(masterplan: dict[str, Any]) -> Iterable[dict[str, Any]]:
    modules = masterplan.get("modules", []) or []
    for module in modules:
        module_id = module.get("id") or module.get("name") or "unknown-module"
        title = module.get("title") or module.get("name") or module_id
        status = module.get("status", "unknown")
        statement = f"COGNITUM module {module_id} ({title}) has governance status {status}."
        yield _claim(
            "module",
            statement,
            {
                "module_id": module_id,
                "title": title,
                "status": status,
                "layer": module.get("layer"),
            },
        )


def _adr_claims(masterplan: dict[str, Any]) -> Iterable[dict[str, Any]]:
    adrs = masterplan.get("adrs", []) or []
    for adr in adrs:
        adr_id = adr.get("id", "unknown-adr")
        title = adr.get("title", adr_id)
        status = adr.get("status", "unknown")
        decision = adr.get("decision", "")
        statement = f"ADR {adr_id} ({title}) is {status}: {decision}"
        yield _claim(
            "adr",
            statement,
            {
                "adr_id": adr_id,
                "title": title,
                "status": status,
                "date": adr.get("date"),
            },
        )


def _privacy_claims(masterplan: dict[str, Any]) -> Iterable[dict[str, Any]]:
    invariants = masterplan.get("privacy_invariants", []) or masterplan.get(
        "privacy", []
    ) or []
    for item in invariants:
        invariant_id = item.get("id", "privacy-invariant")
        title = item.get("title") or item.get("name") or invariant_id
        text = item.get("text") or item.get("description") or item.get("invariant") or ""
        statement = f"Privacy invariant {invariant_id} ({title}) is mandatory: {text}"
        yield _claim(
            "privacy_invariant",
            statement,
            {
                "invariant_id": invariant_id,
                "title": title,
                "status": item.get("status", "mandatory"),
            },
        )


def export_claims(masterplan_path: Path = DEFAULT_MASTERPLAN) -> list[dict[str, Any]]:
    """Return bridge claims exported from the COGNITUM masterplan."""
    with masterplan_path.open("r", encoding="utf-8") as handle:
        masterplan = yaml.safe_load(handle) or {}

    claims: list[dict[str, Any]] = []
    claims.extend(_module_claims(masterplan))
    claims.extend(_adr_claims(masterplan))
    claims.extend(_privacy_claims(masterplan))
    return claims


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masterplan", type=Path, default=DEFAULT_MASTERPLAN)
    parser.add_argument("--limit", type=int, default=0, help="Limit exported claims")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    claims = export_claims(args.masterplan)
    if args.limit > 0:
        claims = claims[: args.limit]

    print(
        json.dumps(
            claims,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
