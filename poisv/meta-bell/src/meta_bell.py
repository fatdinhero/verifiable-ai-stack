"""Meta-Bell Psi measure — wraps the operational Psi from PoISV."""
from __future__ import annotations

from typing import Sequence

from agentsprotocol.psi_test import compute_psi

CHSH_CLASSICAL_BOUND = 2.0
CHSH_QUANTUM_BOUND   = 2.0 * 2**0.5

def meta_bell_psi(error_vectors: Sequence[Sequence[float]]) -> float:
    """Operational Psi (see agentsprotocol.psi_test)."""
    return compute_psi(error_vectors)

def chsh_bound_check(chsh_statistic: float) -> str:
    """Classify a CHSH quantity against the classical / Tsirelson bounds."""
    s = abs(float(chsh_statistic))
    if s <= CHSH_CLASSICAL_BOUND:
        return 'classical'
    if s <= CHSH_QUANTUM_BOUND:
        return 'meta-bell-violation'
    return 'beyond-quantum (numerical error?)'

def bell_violation_test(error_vectors, psi_threshold: float = 0.7) -> bool:
    return meta_bell_psi(error_vectors) >= psi_threshold
