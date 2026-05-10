"""Tests fuer governance/registry.py — deterministische Compliance-Lookups."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from decimal import Decimal
from governance.registry import (get_ta_laerm, calculate_rpn, get_action_priority,
                                  normalize_weights, validate_compliance_claim)
import pytest

def test_ta_laerm_reines_wohngebiet_nacht():
    assert get_ta_laerm("reines_wohn", "nacht") == Decimal("35")

def test_ta_laerm_mischgebiet_tag():
    assert get_ta_laerm("misch", "tag") == Decimal("60")

def test_ta_laerm_ungueltig():
    with pytest.raises(ValueError):
        get_ta_laerm("fantasie", "tag")

def test_rpn_berechnung():
    assert calculate_rpn(8, 5, 3) == 120
