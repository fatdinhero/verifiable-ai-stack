"""Semantic Consistency Score S_con.

Reference: AgentsProtocol DevDocs v1.0, Section 3 (Listing 4).
DOI: 10.5281/zenodo.19642292

Formula:
    S_con(A) = max(0, (cos(v_A, mean(v_kappa)) - tau) / (1 - tau)),
    tau in [0, 1).
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Sequence

import numpy as np


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two non-zero vectors."""
    va = np.asarray(a, dtype=float)
    vb = np.asarray(b, dtype=float)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _stub_embed(text: str, dim: int = 384) -> np.ndarray:
    """Deterministic pseudo-embedding for tests and demos.

    The protocol's reference embedder is sentence-transformers/all-MiniLM-L6-v2
    (dim=384). For testing we derive a deterministic vector from a hash, so the
    S_con pipeline can be exercised without the real model.
    """
    import hashlib
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat-tile the 32-byte digest to the requested dimension
    raw = (h * ((dim // 32) + 1))[:dim]
    vec = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
    vec = vec - 127.5
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def _stub_retrieve_facts(corpus: object, claim_text: str) -> List[str]:
    """Default entity lookup stub.

    In production this queries the IPFS-addressed knowledge corpus for facts
    touching the same entities as the claim. For tests, `corpus` may be a list
    of strings treated directly as the retrieved facts.
    """
    if isinstance(corpus, (list, tuple)):
        return list(corpus)
    if isinstance(corpus, dict):
        return [v for v in corpus.values() if isinstance(v, str)]
    return []


def compute_s_con(
    claim_text: str,
    knowledge_corpus: object,
    embed: Optional[Callable[[str], Sequence[float]]] = None,
    retrieve_facts: Optional[Callable[[object, str], Iterable[str]]] = None,
    tau: float = 0.7,
) -> float:
    """Compute the semantic consistency score S_con for one claim.

    Args:
        claim_text: The statement text from the claim payload.
        knowledge_corpus: The public knowledge corpus (IPFS CID content).
            In testing, a list of fact strings is accepted directly.
        embed: Callable text -> vector. Defaults to the deterministic stub.
        retrieve_facts: Callable (corpus, claim) -> iterable of fact strings.
        tau: Acceptance threshold, tau in [0, 1). Below tau the score is zero.

    Returns:
        S_con in [0.0, 1.0].
    """
    if not 0.0 <= tau < 1.0:
        raise ValueError("tau must be in [0, 1)")

    embed_fn = embed or _stub_embed
    retrieve_fn = retrieve_facts or _stub_retrieve_facts

    v_claim = np.asarray(embed_fn(claim_text), dtype=float)
    facts = list(retrieve_fn(knowledge_corpus, claim_text))
    if not facts:
        return 0.0

    fact_vecs = [np.asarray(embed_fn(f), dtype=float) for f in facts]
    v_mean = np.mean(fact_vecs, axis=0)

    cos_sim = cosine_similarity(v_claim, v_mean)
    return max(0.0, (cos_sim - tau) / (1.0 - tau))
