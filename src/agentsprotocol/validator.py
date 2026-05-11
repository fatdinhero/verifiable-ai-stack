"""End-to-end validator glue: compute S_con + Psi + apply acceptance rule.

Reference: DevDocs Section 5/8, PoISV 3.4.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

from .psi_test import check_acceptance, compute_psi, compute_psi_weighted, compute_error_vectors
from .s_con import compute_s_con


def verify_claim_signature(claim: dict) -> bool:
    """Verify the Ed25519 signature on a claim dict.

    Protocol (DevDocs §2):
        message  = SHA-256(canonical JSON of claim["payload"])
        pubkey   = hex-decoded claim["submitter"]
        signature = hex-decoded claim["signature"]

    Returns True if the signature is valid, False otherwise.
    Requires the `cryptography` package (added to dependencies).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature

        submitter_hex: str = claim["submitter"]
        signature_hex: str = claim["signature"]
        payload = claim["payload"]

        # Canonical payload: sorted keys, no whitespace
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        message = hashlib.sha256(payload_bytes).digest()

        pub_bytes = bytes.fromhex(submitter_hex)
        sig_bytes = bytes.fromhex(signature_hex)

        public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        public_key.verify(sig_bytes, message)
        return True
    except (ImportError, KeyError, ValueError):
        return False
    except Exception:
        # InvalidSignature or any other crypto error
        return False


@dataclass
class BlockDecision:
    accepted: bool
    mean_s_con: float
    psi: float
    reason: str = ""
    weight: float = 0.0


@dataclass
class Validator:
    pubkey: str
    stake: float = 1.0
    embed: Optional[Callable] = None
    retrieve_facts: Optional[Callable] = None

    def score_claim(self, claim_text: str, corpus: object, tau: float = 0.7) -> float:
        return compute_s_con(
            claim_text, corpus, embed=self.embed, retrieve_facts=self.retrieve_facts, tau=tau,
        )

    def error_vector(
        self, control_statements: Sequence[str], reference_scores: Sequence[float],
        corpus: object, tau: float = 0.7,
    ) -> List[float]:
        my_scores = [self.score_claim(s, corpus, tau=tau) for s in control_statements]
        return [abs(my_scores[j] - reference_scores[j]) for j in range(len(reference_scores))]


@dataclass
class BlockProposal:
    claim_texts: List[str]
    corpus: object
    validators: List[Validator] = field(default_factory=list)
    control_statements: Sequence[str] = field(default_factory=list)
    reference_scores: Sequence[float] = field(default_factory=list)
    tau: float = 0.7
    theta_min: float = 0.6
    psi_min: float = 0.7
    zk_proof_verified: bool = True
    use_weighted_psi: bool = True

    def decide(self) -> BlockDecision:
        # Aggregate S_con: each validator scores each claim, then mean over
        # validators first (per claim) then mean over claims.
        per_claim_means: List[float] = []
        for claim_text in self.claim_texts:
            v_scores = [v.score_claim(claim_text, self.corpus, tau=self.tau)
                        for v in self.validators]
            if not v_scores:
                per_claim_means.append(0.0)
            else:
                per_claim_means.append(sum(v_scores) / len(v_scores))
        mean_s_con = sum(per_claim_means) / len(per_claim_means) if per_claim_means else 0.0

        # Psi over validator error vectors on the control set
        if self.control_statements and self.reference_scores and len(self.validators) >= 2:
            error_vectors = [
                v.error_vector(self.control_statements, self.reference_scores,
                               self.corpus, tau=self.tau) for v in self.validators
            ]
            if self.use_weighted_psi:
                psi = compute_psi_weighted(error_vectors, [v.stake for v in self.validators])
            else:
                psi = compute_psi(error_vectors)
        else:
            psi = 1.0

        accepted = check_acceptance(
            per_claim_means, psi,
            theta_min=self.theta_min, psi_min=self.psi_min,
            zk_proof_verified=self.zk_proof_verified,
        )
        reason = (
            "accepted"
            if accepted
            else (
                f"rejected: mean_s_con={mean_s_con:.3f} (>= {self.theta_min}?), "
                f"psi={psi:.3f} (>= {self.psi_min}?), "
                f"zk={self.zk_proof_verified}"
            )
        )
        weight = psi * sum(per_claim_means) if accepted else 0.0
        return BlockDecision(accepted=accepted, mean_s_con=mean_s_con, psi=psi,
                             reason=reason, weight=weight)


def block_weight(psi: float, s_con_scores: Sequence[float]) -> float:
    """Weight(B) = Psi_B * sum_A S_con(A). (DevDocs 5.2, PoISV 3.5)"""
    return float(psi) * float(sum(s_con_scores))
