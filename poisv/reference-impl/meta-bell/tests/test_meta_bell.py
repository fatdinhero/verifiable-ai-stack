from meta_bell.src.meta_bell import (
    meta_bell_psi, chsh_bound_check, bell_violation_test,
)
import pytest

def test_psi_identical_zero():
    assert meta_bell_psi([[0.1, 0.2, 0.3, 0.4]] * 3) == pytest.approx(0.0, abs=1e-9)

def test_chsh_classification():
    assert chsh_bound_check(1.5) == 'classical'
    assert chsh_bound_check(2.5) == 'meta-bell-violation'
    assert chsh_bound_check(3.0) == 'beyond-quantum (numerical error?)'

def test_bell_violation_test():
    independent = [[0.1, 0.2, 0.3, 0.4], [0.3, 0.1, 0.4, 0.2],
                   [0.4, 0.3, 0.2, 0.1]]
    assert isinstance(bell_violation_test(independent), bool)
