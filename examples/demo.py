"""End-to-end AgentsProtocol demo.

Walks through a full validator round:
    1. Submit a claim + JSON schema validation (Pydantic).
    2. Five validators score the claim on a knowledge corpus.
    3. Each validator scores a control set; per-validator error vectors
       are computed; the non-collusion statistic Psi is derived.
    4. Block acceptance rule is applied.
    5. Block weight Weight(B) = Psi * sum(S_con) is computed.
"""
from __future__ import annotations

import json
from pathlib import Path

from agentsprotocol import (
    Claim, compute_psi, compute_psi_weighted, compute_error_vectors,
    check_acceptance,
)
from agentsprotocol.s_con import compute_s_con, _stub_embed
from agentsprotocol.validator import block_weight


HERE = Path(__file__).parent


def make_varied_embed(seed: str):
    """Deterministic validator-specific embedder."""
    def _embed(text: str):
        return _stub_embed(seed + "|" + text)
    return _embed


def main() -> int:
    claim_data = json.loads((HERE / "example_claim.json").read_text(encoding="utf-8"))
    claim = Claim.model_validate(claim_data)
    print(f"Claim {claim.id[:12]}... parsed ok: {claim.payload.statement}")

    control_data = json.loads((HERE / "control_set_v1.json").read_text(encoding="utf-8"))
    control_stmts = [c["statement"] for c in control_data["claims"]]
    control_refs = [c["expectedScore"] for c in control_data["claims"]]

    corpus = [
        "The temperature in Berlin is 20 degrees Celsius today.",
        "Berlin weather: mild 20C, partly sunny.",
        "Meteorological station reports 20C in Berlin-Mitte.",
    ]

    n_validators = 5
    stakes = [1.0, 2.0, 1.5, 3.0, 0.8]
    embeds = [make_varied_embed(f"val-{i}") for i in range(n_validators)]

    # 1. Each validator scores the claim
    claim_scores = []
    for i, emb in enumerate(embeds):
        s = compute_s_con(claim.payload.statement, corpus, embed=emb, tau=0.0)
        claim_scores.append(s)
        print(f"  validator {i}: S_con = {s:.3f}")
    mean_s_con = sum(claim_scores) / len(claim_scores)
    print(f"  mean S_con = {mean_s_con:.3f}")

    # 2. Each validator scores the control set
    validator_scores = []
    for emb in embeds:
        row = [compute_s_con(stmt, corpus, embed=emb, tau=0.0) for stmt in control_stmts]
        validator_scores.append(row)

    error_vectors = compute_error_vectors(validator_scores, control_refs)
    psi_uw = compute_psi(error_vectors)
    psi_w = compute_psi_weighted(error_vectors, stakes)
    print(f"\nPsi (unweighted) = {psi_uw:.4f}")
    print(f"Psi (stake-weighted) = {psi_w:.4f}")

    # 3. Apply acceptance rule (DevDocs 8)
    theta_min, psi_min = 0.6, 0.7
    accepted = check_acceptance([mean_s_con], psi_w,
                                theta_min=theta_min, psi_min=psi_min)
    print(f"\nAcceptance rule: mean_S_con >= {theta_min} AND Psi >= {psi_min}")
    print(f"  -> {'ACCEPTED' if accepted else 'REJECTED'}")

    # 4. Block weight
    w = block_weight(psi_w, [mean_s_con])
    print(f"Block weight = Psi * sum(S_con) = {w:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
