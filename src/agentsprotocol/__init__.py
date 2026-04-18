"""AgentsProtocol reference implementation.

DOI: 10.5281/zenodo.19642292
Bitcoin timestamp: Block 945622, 2026-04-18.
Author: Fatih Dinc <fatdinhero@gmail.com>
License: Apache-2.0 (code) / CC BY 4.0 (docs)
"""
from .s_con import compute_s_con, cosine_similarity
from .psi_test import (
    compute_psi,
    compute_psi_weighted,
    compute_error_vectors,
    check_acceptance,
    attacker_success_bound,
)
from .wise_score import (
    compute_wise_score,
    compute_wise_score_aggregate,
    normalised_truth,
    normalised_context,
    normalised_relevance,
    ethical_compliance,
    attacker_success_probability,
)
from .schemas import Claim, Block, ValidatorOutput, ControlTask, ControlSet

__version__ = "1.0.0"
__author__ = "Fatih Dinc"
__doi__ = "10.5281/zenodo.19642292"

__all__ = [
    "compute_s_con",
    "cosine_similarity",
    "compute_psi",
    "compute_psi_weighted",
    "compute_error_vectors",
    "check_acceptance",
    "attacker_success_bound",
    "compute_wise_score",
    "compute_wise_score_aggregate",
    "normalised_truth",
    "normalised_context",
    "normalised_relevance",
    "ethical_compliance",
    "attacker_success_probability",
    "Claim",
    "Block",
    "ValidatorOutput",
    "ControlTask",
    "ControlSet",
]
