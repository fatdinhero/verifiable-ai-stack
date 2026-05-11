import pytest
from agentsprotocol.wise_score import (
    compute_wise_score, compute_wise_score_aggregate, attacker_success_probability,
)

def test_wise_score_mean():
    v = [0.5, 0.5]; c = [1, 1]; r = [1, 1]; e = [1, 1]
    assert compute_wise_score_aggregate(v, c, r, e) == pytest.approx(
        sum(compute_wise_score(v, c, r, e)) / 2)

def test_attacker_probability_bounded():
    for q in (0.1, 0.3, 0.45):
        for z in (1, 5, 50):
            p = attacker_success_probability(q, z)
            assert 0 <= p <= 1
