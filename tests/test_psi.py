"""Unit tests for Psi-test (PoISV 3.3 / DevDocs 4.2)."""
import math

import numpy as np
import pytest

from agentsprotocol.psi_test import (
    attacker_success_bound,
    check_acceptance,
    compute_error_vectors,
    compute_psi,
    compute_psi_weighted,
)


def test_psi_single_validator_returns_one():
    assert compute_psi([[0.1, 0.2, 0.3]]) == 1.0


def test_psi_empty_returns_one():
    assert compute_psi([]) == 1.0


def test_psi_two_identical_validators_is_zero():
    # identical error vectors -> correlation 1 -> Psi = 0
    e = [[0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4]]
    assert compute_psi(e) == pytest.approx(0.0, abs=1e-9)


def test_psi_anticorrelated_is_zero():
    # anti-correlation (rho = -1) -> |rho| = 1 -> Psi = 0
    e = [[0.1, 0.2, 0.3, 0.4], [0.4, 0.3, 0.2, 0.1]]
    assert compute_psi(e) == pytest.approx(0.0, abs=1e-9)


def test_psi_independent_validators_high():
    rng = np.random.default_rng(42)
    # large k reduces spurious correlation
    n, k = 20, 200
    errors = [rng.uniform(0, 1, size=k).tolist() for _ in range(n)]
    assert compute_psi(errors) > 0.85


def test_psi_constant_errors_treated_as_independent():
    # two constant vectors (std=0) -> handled as rho=0
    e = [[0.5] * 5, [0.2] * 5]
    assert compute_psi(e) == pytest.approx(1.0)


def test_psi_range_bounded():
    rng = np.random.default_rng(0)
    for _ in range(5):
        errors = [rng.uniform(0, 1, size=10).tolist() for _ in range(4)]
        psi = compute_psi(errors)
        assert 0.0 <= psi <= 1.0


def test_psi_weighted_equals_unweighted_with_equal_stakes():
    errors = [[0.1, 0.3, 0.2], [0.2, 0.1, 0.4], [0.4, 0.2, 0.3]]
    psi_uw = compute_psi(errors)
    psi_w = compute_psi_weighted(errors, [1.0, 1.0, 1.0])
    assert psi_uw == pytest.approx(psi_w, abs=1e-9)


def test_psi_weighted_stake_mismatch():
    with pytest.raises(ValueError):
        compute_psi_weighted([[0.1], [0.2]], [1.0])


def test_psi_weighted_zero_stakes():
    assert compute_psi_weighted([[0.1, 0.2], [0.2, 0.1]], [0.0, 0.0]) == 0.0


def test_error_vectors_shape():
    scores = [[0.9, 0.8, 1.0], [0.7, 0.95, 0.88]]
    ref = [1.0, 0.9, 0.95]
    ev = compute_error_vectors(scores, ref)
    assert len(ev) == 2
    assert np.allclose(ev[0], [0.1, 0.1, 0.05])
    assert np.allclose(ev[1], [0.3, 0.05, 0.07])


def test_error_vectors_shape_mismatch_raises():
    with pytest.raises(ValueError):
        compute_error_vectors([[0.1, 0.2]], [1.0])


def test_acceptance_all_conditions_met():
    assert check_acceptance([0.7, 0.8, 0.6], psi=0.8,
                            theta_min=0.6, psi_min=0.7, zk_proof_verified=True)


def test_acceptance_fail_mean():
    assert not check_acceptance([0.3, 0.4], psi=0.9,
                                theta_min=0.6, psi_min=0.7)


def test_acceptance_fail_psi():
    assert not check_acceptance([0.9, 0.8], psi=0.5,
                                theta_min=0.6, psi_min=0.7)


def test_acceptance_fail_zk():
    assert not check_acceptance([0.9, 0.8], psi=0.9,
                                zk_proof_verified=False)


def test_acceptance_empty_block_rejected():
    assert not check_acceptance([], psi=1.0)


def test_attacker_bound_decreasing_in_k():
    # More control tasks -> tighter Psi bound -> smaller P_total
    p1 = attacker_success_bound(0.3, 32)
    p2 = attacker_success_bound(0.3, 128)
    assert p2 < p1


def test_attacker_bound_nontrivial_for_all_q_below_half():
    # Decomposed formula is well-defined for all q in (0, 0.5)
    for q in (0.1, 0.2, 0.3, 0.4, 0.49):
        p = attacker_success_bound(q, 64)
        assert 0.0 < p < 1.0


def test_attacker_bound_range():
    for q in (0.01, 0.1, 0.3, 0.49):
        for k in (8, 32, 128):
            p = attacker_success_bound(q, k)
            assert 0.0 <= p <= 1.0


def test_attacker_bound_invalid():
    with pytest.raises(ValueError):
        attacker_success_bound(-0.1, 32)
    with pytest.raises(ValueError):
        attacker_success_bound(0.3, 0)


def test_paper_table_values():
    # PoISV §5.2 security table — all five rows must be reproduced exactly.
    # Decomposed formula: P_total = P_nakamoto(q, z=6) * P_psi(k, psi_min=0.7)
    cases = [
        (0.10,  32, 1e-12),
        (0.20,  32, 1e-8),
        (0.30,  64, 1e-7),
        (0.40,  64, 1e-4),
        (0.49, 128, 1e-3),
    ]
    for q, k, threshold in cases:
        p = attacker_success_bound(q, k, psi_min=0.7, z=6, delta_krit=1.0)
        assert p < threshold, (
            f"Table row q={q} k={k}: got {p:.3e}, expected < {threshold:.0e}"
        )
