"""FastAPI backend for the Meta-Bell Ψ detector.

Endpoints:
    POST /validate  — compute S_con, Psi, WiseScore for a claim
    GET  /health    — liveness check

Run locally:
    pip install fastapi uvicorn
    uvicorn detect.api:app --reload --port 8000

The endpoint uses the Python reference implementations from
src/agentsprotocol/ directly. No external model is required —
the stub embedder (SHA-256 tiling) is used by default.
"""
from __future__ import annotations

import math
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agentsprotocol.s_con import compute_s_con, _stub_embed
from agentsprotocol.psi_test import compute_psi, compute_error_vectors
from agentsprotocol.wise_score import compute_wise_score_aggregate, attacker_success_probability

app = FastAPI(title="AgentsProtocol Detect API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Default corpus used when no external knowledge corpus is provided.
# In production this would be loaded from IPFS or a local cache.
_DEFAULT_CORPUS = [
    "Scientific claims should be supported by peer-reviewed evidence.",
    "Statistical data requires a cited source and methodology.",
    "Extraordinary claims require extraordinary evidence.",
    "Consensus among independent experts increases credibility.",
    "Verifiable predictions strengthen a claim's validity.",
]

# Simulated validator error vectors for Psi computation.
# In production these come from real validator nodes via the RPC layer.
_N_VALIDATORS = 5
_CONTROL_SET_SIZE = 10


class ValidateRequest(BaseModel):
    claim: str
    category: Optional[str] = "general"
    corpus: Optional[list[str]] = None


class ValidateResponse(BaseModel):
    s_con: float
    psi: float
    wise_score: float
    manipulation_risk: float
    attacker_success_prob: float
    accepted: bool
    confidence: float
    unverified: bool
    detail: str
    sources: list[str]


@app.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> ValidateResponse:
    corpus = req.corpus if req.corpus else _DEFAULT_CORPUS

    # S_con — semantic consistency of claim against corpus
    s = compute_s_con(
        claim_text=req.claim,
        knowledge_corpus=corpus,
        embed=_stub_embed,
        tau=0.0,  # no threshold clipping — return raw score
    )

    # Psi — simulate N validators scoring the claim against a control set
    # Each validator's error vector: |score_i(d_j) - reference(d_j)|
    import numpy as np
    rng = np.random.default_rng(seed=abs(hash(req.claim)) % (2**31))

    # Reference scores for control set (ground truth)
    reference = rng.uniform(0.6, 1.0, _CONTROL_SET_SIZE)

    # Validator scores: independent validators cluster near reference;
    # coordinated validators share a systematic bias
    validator_scores = []
    for i in range(_N_VALIDATORS):
        noise = rng.normal(0, 0.05, _CONTROL_SET_SIZE)
        validator_scores.append((reference + noise).clip(0, 1).tolist())

    error_vecs = compute_error_vectors(validator_scores, reference.tolist())
    psi = compute_psi(error_vecs)

    # WiseScore W(i) = T × C × R × E  (PoWW §4)
    # Use S_con as T proxy; derive C, R, E from text features
    ethics_map = {"general": 1.0, "finance": 0.90, "politics": 0.86,
                  "science": 0.95, "crypto": 0.87}
    t_val = s
    c_val = min(1.0, 0.68 + 0.1 * (len(req.claim.split()) >= 8))
    r_val = min(1.0, 0.55 + 0.3 * s)
    e_val = ethics_map.get(req.category or "general", 1.0)
    w = compute_wise_score_aggregate([t_val], [c_val], [r_val], [e_val])

    # Attacker success probability (PoWW §11)
    q = max(0.0, 1.0 - psi)   # attacker hash-rate proxy
    z = max(1, round(w * 10))  # lead blocks proportional to WiseScore
    asp = attacker_success_probability(q=q, z=z)

    # Manipulation risk 0–100
    risk = round((1.0 - psi) * 100 * (1.5 if s < 0.5 else 1.0))
    risk = min(100, max(0, risk))

    # Acceptance rule (DevDocs §8): W >= theta_min AND Psi >= psi_min
    theta_min = 0.60
    psi_min = 0.70
    accepted = w >= theta_min and psi >= psi_min

    # Confidence: high when both scores are well above threshold
    confidence = min(1.0, (w / theta_min) * 0.5 + (psi / psi_min) * 0.5) if accepted else \
                 min(0.79, (w + psi) / 2)
    unverified = confidence < 0.8

    detail = (
        f"S_con={s:.3f} (stub embedder), Psi={psi:.3f} ({_N_VALIDATORS} simulated validators), "
        f"W={w:.3f}. "
        + ("Accepted by protocol." if accepted else
           f"Rejected: {'WiseScore below θ_min=0.60' if w < theta_min else 'Ψ below ψ_min=0.70'}.")
    )

    return ValidateResponse(
        s_con=round(s, 4),
        psi=round(psi, 4),
        wise_score=round(w, 4),
        manipulation_risk=float(risk),
        attacker_success_prob=round(asp, 4),
        accepted=accepted,
        confidence=round(confidence, 4),
        unverified=unverified,
        detail=detail,
        sources=[
            "doi.org/10.5281/zenodo.19642292",
            "agentsprotocol.org",
        ],
    )


@app.get("/")
def root() -> dict:
    return {
        "service": "agentsprotocol-detect-api",
        "version": "1.3.0",
        "status": "ok",
        "endpoints": {
            "validate": "POST /validate",
            "health": "GET /health",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.3.0"}
