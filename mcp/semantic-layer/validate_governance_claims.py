#!/usr/bin/env python3
"""Validate exported COGNITUM governance claims with AgentsProtocol primitives."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTSPROTOCOL_SRC = REPO_ROOT / "agentsprotocol" / "src"
if str(AGENTSPROTOCOL_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTSPROTOCOL_SRC))

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from agentsprotocol import check_acceptance, compute_psi, compute_s_con  # noqa: E402
from governance_claims import DEFAULT_MASTERPLAN, export_claims  # noqa: E402


def _knowledge_corpus(claims: list[dict[str, Any]]) -> list[str]:
    """Build a simple local corpus from governance statements.

    This keeps the bridge deterministic. A future production version can replace
    it with an IPFS-addressed or signed governance corpus.
    """
    return [claim["statement"] for claim in claims]


def validate_claims(
    *,
    limit: int = 0,
    theta_min: float = 0.6,
    psi_min: float = 0.7,
) -> dict[str, Any]:
    claims = export_claims(DEFAULT_MASTERPLAN)
    if limit > 0:
        claims = claims[:limit]

    corpus = _knowledge_corpus(claims)
    scored_claims = []
    scores = []
    for claim in claims:
        score = compute_s_con(claim["statement"], corpus, tau=0.1)
        scores.append(score)
        scored_claims.append(
            {
                "id": claim["id"],
                "kind": claim["kind"],
                "statement": claim["statement"],
                "s_con": round(score, 6),
            }
        )

    # Deterministic placeholder error vectors for the bridge smoke path. Real
    # validator outputs should replace this once multiple validators are wired.
    error_vectors = [
        [abs(score - 1.0) for score in scores],
        [abs(score - 0.95) for score in scores],
    ]
    psi = compute_psi(error_vectors)
    accepted = check_acceptance(scores, psi, theta_min=theta_min, psi_min=psi_min)

    return {
        "source": "cognitum/governance/masterplan.yaml",
        "protocol": "agentsprotocol",
        "claim_count": len(scored_claims),
        "theta_min": theta_min,
        "psi_min": psi_min,
        "mean_s_con": round(sum(scores) / len(scores), 6) if scores else 0.0,
        "psi": round(psi, 6),
        "accepted": accepted,
        "claims": scored_claims,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Limit validated claims")
    parser.add_argument("--theta-min", type=float, default=0.6)
    parser.add_argument("--psi-min", type=float, default=0.7)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    report = validate_claims(
        limit=args.limit,
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
