from agentsprotocol.psi_test import check_acceptance, compute_psi
from agentsprotocol.validator import block_weight

def test_end_to_end():
    s = [0.8, 0.7, 0.9]
    psi = compute_psi([[0.1, 0.2, 0.3, 0.1],
                       [0.3, 0.1, 0.2, 0.2],
                       [0.2, 0.3, 0.1, 0.3]])
    assert 0.0 <= psi <= 1.0
    assert check_acceptance(s, psi, theta_min=0.5, psi_min=0.3)
    assert block_weight(psi, s) > 0
