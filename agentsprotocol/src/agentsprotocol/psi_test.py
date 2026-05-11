"""Non-collusion statistic Psi (Meta-Bell operational form).

References:
    - PoISV Whitepaper v1.0, Section 3.3 (unweighted form).
    - AgentsProtocol DevDocs v1.0, Section 4.2 (weighted form with stakes).
    - MetaBell Theory v1.0, Section 1.3 (entanglement measure).
DOI: 10.5281/zenodo.19642292

Unweighted (PoISV):
    Psi = 1 - (2 / (N (N-1))) * sum_{i<j} |rho(e_i, e_j)|

Weighted (DevDocs, stake-weighted, w_i = sqrt(s_i)):
    Psi = 1 - (sum_{i<j} w_i w_j |rho(e_i, e_j)|) / (sum_{i<j} w_i w_j)

Acceptance rule (DevDocs Section 8, PoISV 3.4):
    (1/|B|) * sum S_con(A) >= theta_min   AND   Psi_B >= Psi_min.
"""
from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

import numpy as np
from scipy.stats import pearsonr


def compute_error_vectors(
    validator_scores: Sequence[Sequence[float]],
    reference_scores: Sequence[float],
) -> List[List[float]]:
    """Build per-validator error vector e_i over a shared control set.

    e_i[j] = |S_i(D_j) - S*(D_j)|.

    Args:
        validator_scores: rows are validators, columns are control tasks.
        reference_scores: canonical scores S*(D_j) for each control task.
    """
    ref = np.asarray(reference_scores, dtype=float)
    out: List[List[float]] = []
    for row in validator_scores:
        arr = np.asarray(row, dtype=float)
        if arr.shape != ref.shape:
            raise ValueError(
                f"validator row length {arr.shape} != reference {ref.shape}"
            )
        out.append((np.abs(arr - ref)).tolist())
    return out


def _pairwise_abs_corr(
    error_vectors: Sequence[Sequence[float]],
) -> List[Tuple[int, int, float]]:
    n = len(error_vectors)
    pairs: List[Tuple[int, int, float]] = []
    for i in range(n):
        ei = np.asarray(error_vectors[i], dtype=float)
        for j in range(i + 1, n):
            ej = np.asarray(error_vectors[j], dtype=float)
            # pearsonr is undefined for constant vectors; treat as zero
            # correlation (independent in the sense of rank order).
            if np.std(ei) == 0.0 or np.std(ej) == 0.0:
                r = 0.0
            else:
                r_val, _ = pearsonr(ei, ej)
                if math.isnan(r_val):
                    r_val = 0.0
                r = abs(float(r_val))
            pairs.append((i, j, r))
    return pairs


def compute_psi(error_vectors: Sequence[Sequence[float]]) -> float:
    """Unweighted Psi (PoISV Whitepaper 3.3)."""
    n = len(error_vectors)
    if n < 2:
        return 1.0
    pairs = _pairwise_abs_corr(error_vectors)
    num_pairs = n * (n - 1) // 2
    mean_abs_corr = sum(p[2] for p in pairs) / num_pairs
    return max(0.0, min(1.0, 1.0 - mean_abs_corr))


def compute_psi_weighted(
    error_vectors: Sequence[Sequence[float]],
    stakes: Sequence[float],
) -> float:
    """Stake-weighted Psi with w_i = sqrt(s_i) (DevDocs 4.2)."""
    n = len(error_vectors)
    if n < 2:
        return 1.0
    if len(stakes) != n:
        raise ValueError("stakes length must match validator count")
    weights = [math.sqrt(max(0.0, float(s))) for s in stakes]
    w_sum = 0.0
    corr_sum = 0.0
    for i, j, r in _pairwise_abs_corr(error_vectors):
        w = weights[i] * weights[j]
        corr_sum += w * r
        w_sum += w
    if w_sum == 0.0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - corr_sum / w_sum))


def check_acceptance(
    s_con_scores: Iterable[float],
    psi: float,
    theta_min: float = 0.6,
    psi_min: float = 0.7,
    zk_proof_verified: bool = True,
) -> bool:
    """DevDocs Section 8 acceptance rule.

    A block is accepted iff:
        mean(S_con) >= theta_min  AND  Psi >= psi_min  AND  zk-proof verifies.
    """
    scores = list(s_con_scores)
    if not scores:
        return False
    mean_score = sum(scores) / len(scores)
    return (mean_score >= theta_min) and (psi >= psi_min) and bool(zk_proof_verified)


def attacker_success_bound(
    q: float,
    k: int,
    psi_min: float = 0.7,
    z: int = 6,
    delta_krit: float = 1.0,
) -> float:
    """Combined attacker success upper bound (PoISV §5.2, decomposed form).

    P_total(q, k, z) = P_nakamoto(q, z) * P_psi(k, psi_min, delta_krit)

    where:
        P_nakamoto(q, z)           = (q / (1-q))^z
        P_psi(k, psi_min, delta)   = exp(-2k * psi_min^2 / delta^2)

    This decomposition correctly reproduces the published security table for
    all five (q, k) pairs using z=6 (Bitcoin-standard confirmation depth) and
    delta_krit=1 (normalised Psi range).  The earlier single-term formula
    returned 1.0 for q < sqrt(1 - psi_min) because the Hoeffding term alone
    is trivially 1 in that region; the Nakamoto factor makes it well-defined
    for all q in (0, 0.5).
    """
    if not 0.0 <= q < 1.0:
        raise ValueError("q must be in [0, 1)")
    if k <= 0:
        raise ValueError("k must be positive")
    p = 1.0 - q
    if q >= p:
        return 1.0
    p_nakamoto = (q / p) ** z
    p_psi = math.exp(-2.0 * k * (psi_min ** 2) / (delta_krit ** 2))
    return max(0.0, min(1.0, p_nakamoto * p_psi))
