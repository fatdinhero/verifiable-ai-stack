#!/usr/bin/env python3
"""Compatibility wrapper for COGNITUM governance claim export.

The canonical implementation lives in
`cognitum/scripts/export_governance_claims.py` because COGNITUM owns the
governance Single Source of Truth. This MCP-layer script remains as a routing
entry point for future VeriMCP tooling.
"""

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
)


def export_claims(masterplan_path: Path = DEFAULT_MASTERPLAN) -> list[dict]:
    """Return bridge claims exported from the COGNITUM masterplan."""
    return export_governance_claims(masterplan_path)


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
