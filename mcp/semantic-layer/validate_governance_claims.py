#!/usr/bin/env python3
"""Compatibility wrapper for COGNITUM governance claim validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COGNITUM_SCRIPTS = REPO_ROOT / "cognitum" / "scripts"
if str(COGNITUM_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(COGNITUM_SCRIPTS))

from export_governance_claims import (  # noqa: E402
    DEFAULT_MASTERPLAN,
    export_governance_claims,
    validate_governance_claims,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Limit validated claims")
    parser.add_argument("--tau", type=float, default=0.1)
    parser.add_argument("--theta-min", type=float, default=0.6)
    parser.add_argument("--psi-min", type=float, default=0.7)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    claims = export_governance_claims(DEFAULT_MASTERPLAN)
    if args.limit > 0:
        claims = claims[: args.limit]

    report = validate_governance_claims(
        claims,
        tau=args.tau,
        theta_min=args.theta_min,
        psi_min=args.psi_min,
    )
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
