"""Unit tests for WiseScore (PoWW Whitepaper v2 Section 4 / 11)."""
import numpy as np
import pytest

from agentsprotocol.wise_score import (
    attacker_success_probability,
    compute_wise_score,
    compute_wise_score_aggregate,
    ethical_compliance,
    normalised_context,
    normalised_relevance,
    normalised_truth,
    attacker_probability_table,
)


def test_normalised_truth_sums_to_one():
    t = normalised_truth([0.1, 0.5, 0.9, 0.2])
    assert sum(t) == pytest.approx(1.0)


def test_normalised_truth_higher_v_higher_t():
    t = normalised_truth([0.1, 0.9])
    assert t[1] > t[0]


def test_normalised_truth_invalid_alpha():
    with pytest.raises(ValueError):
        normalised_truth([0.1, 0.2], alpha=0.0)


def test_normalised_context_sums_to_one():
    c = normalised_context([2.0, 3.0, 5.0])
    assert sum(c) == pytest.approx(1.0)


def test_normalised_context_zero_sum():
    assert normalised_context([0.0, 0.0]) == [0.0, 0.0]


def test_normalised_context_negative_raises():
    with pytest.raises(ValueError):
        normalised_context([1.0, -0.5])


def test_normalised_relevance_log():
    r = normalised_relevance([0.0, 1.0, np.e - 1.0])
    assert r[0] == pytest.approx(0.0)
    assert r[1] == pytest.approx(np.log(2.0))
    assert r[2] == pytest.approx(1.0)


def test_normalised_relevance_negative_raises():
    with pytest.raises(ValueError):
        normalised_relevance([1.0, -0.1])


def test_ethical_compliance_bounds():
    assert ethical_compliance([0.0, 0.5, 1.0]) == [0.0, 0.5, 1.0]
    with pytest.raises(ValueError):
        ethical_compliance([0.5, 1.5])


def test_wise_score_zero_ethics_kills_contribution():
    # PoWW: ethically problematic unit should receive near-zero score
    v = [0.9, 0.9]
    c = [1.0, 1.0]
    r = [5.0, 5.0]
    e = [1.0, 0.0]  # second unit ethically non-compliant
    w = compute_wise_score(v, c, r, e)
    assert w[1] == 0.0
    assert w[0] > 0


def test_wise_score_length_mismatch():
    with pytest.raises(ValueError):
        compute_wise_score([0.5], [1.0], [1.0, 2.0], [1.0])


def test_wise_score_aggregate_is_mean():
    v = [0.5, 0.5, 0.5]
    c = [1.0, 1.0, 1.0]
    r = [1.0, 1.0, 1.0]
    e = [1.0, 1.0, 1.0]
    agg = compute_wise_score_aggregate(v, c, r, e)
    manual = sum(compute_wise_score(v, c, r, e)) / 3
    assert agg == pytest.approx(manual)


def test_attacker_probability_decreasing_in_z():
    qs = [0.1, 0.2, 0.3, 0.4]
    for q in qs:
        vals = [attacker_success_probability(q, z) for z in (1, 2, 5, 10, 20)]
        # monotonically non-increasing with z (for q < 0.5)
        for a, b in zip(vals, vals[1:]):
            assert b <= a + 1e-9


def test_attacker_probability_q_geq_half_is_one():
    assert attacker_success_probability(0.5, 10) == 1.0
    assert attacker_success_probability(0.6, 10) == 1.0


def test_attacker_probability_range():
    for q in (0.05, 0.1, 0.2, 0.3, 0.4):
        for z in (1, 5, 10, 50):
            p = attacker_success_probability(q, z)
            assert 0.0 <= p <= 1.0


def test_attacker_probability_z_zero():
    # with zero confirmations the attacker needs 0 blocks: trivial catch-up
    # our formulation returns 0 for q == 0, otherwise 1 via the base case
    assert attacker_success_probability(0.0, 0) == 0.0


def test_attacker_probability_invalid():
    with pytest.raises(ValueError):
        attacker_success_probability(1.5, 5)
    with pytest.raises(ValueError):
        attacker_success_probability(0.2, -1)


def test_attacker_probability_table_dimensions():
    table = attacker_probability_table(qs=(0.1, 0.3), zs=(1, 5))
    assert len(table) == 4
    for q, z, p in table:
        assert 0.0 <= p <= 1.0
