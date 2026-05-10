from governance.registry import (get_ta_laerm, calculate_rpn, get_action_priority,
                                  normalize_weights, validate_compliance_claim)"""Tests fuer governance/registry.py — deterministische Compliance-Lookups."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from decimal import Decimal
from governance.registry import (get_ta_laerm, calculate_rpn, get_action_priority,
                                  run_nwa, GEG_PRIMAERENERGIE, BEG_STUFEN)
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

def test_rpn_grenzen():
    with pytest.raises(ValueError):
        calculate_rpn(0, 5, 3)
    with pytest.raises(ValueError):
        calculate_rpn(5, 11, 3)

def test_action_priority_high_severity():
    assert get_action_priority(9, 3, 3) == "H"

def test_action_priority_low():
    assert get_action_priority(2, 2, 2) == "L"

def test_nwa_basic():
    result = run_nwa(
        kriterien={},
        gewichte={"a": 0.5, "b": 0.5},
        optionen={"x": {"a": 4, "b": 2}, "y": {"a": 2, "b": 4}}
    )
    assert result["x"] == result["y"]  # Gleiche Gewichte, gespiegelte Werte

def test_geg_faktoren():
    assert GEG_PRIMAERENERGIE["strom"] == Decimal("1.8")
    assert GEG_PRIMAERENERGIE["holz"] == Decimal("0.2")

def test_beg_stufen():
    assert "40" in BEG_STUFEN
    assert BEG_STUFEN["40"]["q_p"] == Decimal("40")

# === VDI 2225 Tests ===

def test_vdi2225_score_basic():
    from governance.registry import vdi2225_score
    score = vdi2225_score(
        {"tech": 4, "wirt": 3}, {"tech": 0.6, "wirt": 0.4}, skala_max=4
    )
    # (4*0.6 + 3*0.4) / 4 = (2.4+1.2)/4 = 0.9
    assert score == 0.9

def test_vdi2225_evaluate_gate():
    from governance.registry import vdi2225_evaluate
    result = vdi2225_evaluate(
        optionen={
            "A": {"tech": 4, "wirt": 3},
            "B": {"tech": 2, "wirt": 1},
        },
        gewichte={"tech": 0.6, "wirt": 0.4},
        mindest_score=0.5
    )
    assert result["best"] == "A"
    assert result["gate_passed"] is True

def test_vdi2225_gate_fail():
    from governance.registry import vdi2225_evaluate
    result = vdi2225_evaluate(
        optionen={"X": {"tech": 1, "wirt": 1}},
        gewichte={"tech": 0.5, "wirt": 0.5},
        mindest_score=0.9
    )
    assert result["gate_passed"] is False

# === Morphologischer Kasten Tests ===

def test_morphologie_basic():
    from governance.registry import morphologischer_kasten
    matrix = {"Energie": ["Batterie", "Netz"], "UI": ["Touch", "CLI"]}
    varianten = morphologischer_kasten(matrix, max_varianten=10)
    assert len(varianten) == 4  # 2x2 = 4

def test_morphologie_ausschluss():
    from governance.registry import morphologischer_kasten
    matrix = {"Energie": ["Batterie", "Netz"], "UI": ["Touch", "CLI"]}
    varianten = morphologischer_kasten(matrix, ausschluss={"Energie": ["Batterie"]})
    assert all(v["Energie"] != "Batterie" for v in varianten)
    assert len(varianten) == 2

def test_morphologie_max():
    from governance.registry import morphologischer_kasten
    matrix = {"A": ["1","2","3"], "B": ["x","y","z"], "C": ["a","b","c"]}
    varianten = morphologischer_kasten(matrix, max_varianten=5)
    assert len(varianten) == 5
