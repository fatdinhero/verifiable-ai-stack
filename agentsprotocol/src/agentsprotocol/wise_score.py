"""Proof of WiseWork — WiseScore and attacker-success probability.

Reference: PoWW Whitepaper v2.0, Section 4 and Section 11.
DOI: 10.5281/zenodo.19642292

An information unit i = (v, c, r, e):
    T(i) = exp(alpha * v_i) / sum_j exp(alpha * v_j)        softmax truth
    C(i) = c_i / sum_j c_j                                   context share
    R(i) = log(1 + r_i)                                      dampened relevance
    E(i) = e_i                                               ethical compliance
    W(i) = T(i) * C(i) * R(i) * E(i)                         WiseScore
    PoWW(block) = (1/|I|) * sum_i W(i)                       aggregate
"""
from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from scipy.stats import poisson


def normalised_truth(v_values: Sequence[float], alpha: float = 1.0) -> List[float]:
    """T(i) softmax over truth candidates v_i in [0,1]."""
    if alpha <= 0.0:
        raise ValueError("alpha must be positive")
    v = np.asarray(v_values, dtype=float)
    # numerically stable softmax
    shifted = alpha * v - np.max(alpha * v)
    exp_v = np.exp(shifted)
    return (exp_v / exp_v.sum()).tolist()


def normalised_context(c_values: Sequence[float]) -> List[float]:
    """C(i) = c_i / sum_j c_j, c_i >= 0."""
    c = np.asarray(c_values, dtype=float)
    if np.any(c < 0):
        raise ValueError("context weights must be non-negative")
    total = c.sum()
    if total == 0.0:
        return [0.0] * len(c)
    return (c / total).tolist()


def normalised_relevance(r_values: Sequence[float]) -> List[float]:
    """R(i) = log(1 + r_i), r_i >= 0."""
    r = np.asarray(r_values, dtype=float)
    if np.any(r < 0):
        raise ValueError("relevance values must be non-negative")
    return np.log1p(r).tolist()


def ethical_compliance(e_values: Sequence[float]) -> List[float]:
    """E(i) = e_i in [0,1]."""
    e = np.asarray(e_values, dtype=float)
    if np.any((e < 0) | (e > 1)):
        raise ValueError("ethical compliance must be in [0, 1]")
    return e.tolist()


def compute_wise_score(
    v_values: Sequence[float],
    c_values: Sequence[float],
    r_values: Sequence[float],
    e_values: Sequence[float],
    alpha: float = 1.0,
) -> List[float]:
    """Compute W(i) for all information units in a block."""
    n = len(v_values)
    if not (len(c_values) == len(r_values) == len(e_values) == n):
        raise ValueError("all four component vectors must be equal length")
    t = normalised_truth(v_values, alpha=alpha)
    c = normalised_context(c_values)
    r = normalised_relevance(r_values)
    e = ethical_compliance(e_values)
    return [t[i] * c[i] * r[i] * e[i] for i in range(n)]


def compute_wise_score_aggregate(
    v_values: Sequence[float],
    c_values: Sequence[float],
    r_values: Sequence[float],
    e_values: Sequence[float],
    alpha: float = 1.0,
) -> float:
    """PoWW(block) = arithmetic mean of W(i)."""
    w = compute_wise_score(v_values, c_values, r_values, e_values, alpha=alpha)
    if not w:
        return 0.0
    return sum(w) / len(w)


def attacker_success_probability(q: float, z: int) -> float:
    """Nakamoto-style Gambler's Ruin probability of attacker catching up.

    Reference: PoWW Whitepaper v2.0 Section 11 (analogous to Bitcoin
    Section 11). With p = 1 - q the probability of the honest chain
    extending and lambda = z * (q / p):

        P_catchup = 1 - sum_{k=0..z} [ Poisson(k; lambda) * (1 - (q/p)^(z-k)) ].

    If q >= p, the attacker is guaranteed to catch up (P = 1).
    """
    if not 0.0 <= q <= 1.0:
        raise ValueError("q must be in [0, 1]")
    if z < 0:
        raise ValueError("z must be non-negative")
    p = 1.0 - q
    if q >= p:
        return 1.0
    if q == 0.0 or z == 0:
        return 0.0 if q == 0.0 else 1.0 if q >= p else 1.0 - _zero_case(q, z)
    lam = z * (q / p)
    total = 0.0
    ratio = q / p
    for k in range(z + 1):
        poisson_pmf = poisson.pmf(k, lam)
        # probability attacker catches up given lead difference (z - k)
        catch_up_from_gap = ratio ** (z - k)
        total += poisson_pmf * (1.0 - catch_up_from_gap)
    return max(0.0, min(1.0, 1.0 - total))


def _zero_case(q: float, z: int) -> float:
    """Helper to avoid division-by-zero branches in edge cases."""
    return 1.0 if q >= 1.0 - q else (q / (1.0 - q)) ** z


def attacker_probability_table(
    qs: Iterable[float] = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45),
    zs: Iterable[int] = (1, 2, 3, 5, 10, 20, 50, 100),
) -> List[Tuple[float, int, float]]:
    """Reproduce q/z/P(catch_up) table from PoWW appendix."""
    out: List[Tuple[float, int, float]] = []
    for q in qs:
        for z in zs:
            out.append((q, z, attacker_success_probability(q, z)))
    return out
