"""pytest — alle 12 CNA-Normregeln"""
from __future__ import annotations

import pytest
from cognitum.cna.rules import RULES, Rule, RuleResult


def _get(rule_id: str) -> Rule:
    for r in RULES:
        if r.rule_id == rule_id:
            return r
    raise KeyError(rule_id)


# ── Metaprüfungen ──────────────────────────────────────────────────────────

def test_exactly_12_rules():
    assert len(RULES) == 12


def test_all_rule_ids_unique():
    ids = [r.rule_id for r in RULES]
    assert len(ids) == len(set(ids))


def test_missing_param_returns_fail_with_zero_confidence():
    rule = RULES[0]
    result = rule.evaluate({})
    assert not result.passed
    assert result.confidence == 0.0
    assert result.value is None


# ── GEG §71 ───────────────────────────────────────────────────────────────

class TestGEG71Abstand:
    def test_pass_exact(self):
        assert _get("GEG-71-01").evaluate({"abstand_m": 3.0}).passed

    def test_pass_above(self):
        assert _get("GEG-71-01").evaluate({"abstand_m": 5.0}).passed

    def test_fail_below(self):
        assert not _get("GEG-71-01").evaluate({"abstand_m": 2.99}).passed


class TestGEG71Tagpegel:
    def test_pass_exact(self):
        assert _get("GEG-71-02").evaluate({"tagpegel_db": 50.0}).passed

    def test_pass_below(self):
        assert _get("GEG-71-02").evaluate({"tagpegel_db": 44.0}).passed

    def test_fail_above(self):
        assert not _get("GEG-71-02").evaluate({"tagpegel_db": 50.1}).passed


class TestGEG71Nachtpegel:
    def test_pass_exact(self):
        assert _get("GEG-71-03").evaluate({"nachtpegel_db": 35.0}).passed

    def test_fail_above(self):
        assert not _get("GEG-71-03").evaluate({"nachtpegel_db": 35.1}).passed


# ── GEG §72 ───────────────────────────────────────────────────────────────

class TestGEG72JAZ:
    def test_pass_exact(self):
        assert _get("GEG-72-01").evaluate({"jaz": 3.5}).passed

    def test_pass_above(self):
        assert _get("GEG-72-01").evaluate({"jaz": 4.2}).passed

    def test_fail_below(self):
        assert not _get("GEG-72-01").evaluate({"jaz": 3.49}).passed


# ── GEG §74 ───────────────────────────────────────────────────────────────

class TestGEG74Dokumentation:
    def test_pass_true(self):
        assert _get("GEG-74-01").evaluate({"dokumentation_vollstaendig": True}).passed

    def test_fail_false(self):
        assert not _get("GEG-74-01").evaluate({"dokumentation_vollstaendig": False}).passed

    def test_fail_truthy_string(self):
        # must be exactly True, not a truthy string
        assert not _get("GEG-74-01").evaluate({"dokumentation_vollstaendig": "yes"}).passed


# ── KfW-BEG ───────────────────────────────────────────────────────────────

class TestKfWVorlauftemp:
    def test_pass_exact(self):
        assert _get("KFW-BEG-01").evaluate({"vorlauftemp_c": 55.0}).passed

    def test_pass_below(self):
        assert _get("KFW-BEG-01").evaluate({"vorlauftemp_c": 35.0}).passed

    def test_fail_above(self):
        assert not _get("KFW-BEG-01").evaluate({"vorlauftemp_c": 55.1}).passed


class TestKfWHeizstab:
    def test_pass_below(self):
        assert _get("KFW-BEG-02").evaluate({"heizstab_prozent": 4.99}).passed

    def test_fail_exact_boundary(self):
        # strict <5, so 5.0 must fail
        assert not _get("KFW-BEG-02").evaluate({"heizstab_prozent": 5.0}).passed

    def test_fail_above(self):
        assert not _get("KFW-BEG-02").evaluate({"heizstab_prozent": 6.0}).passed


class TestKfWWaermebruecken:
    def test_pass_below(self):
        assert _get("KFW-BEG-03").evaluate({"waermebruecken_w_mk": 0.19}).passed

    def test_fail_exact_boundary(self):
        # strict <0.2, so 0.2 must fail
        assert not _get("KFW-BEG-03").evaluate({"waermebruecken_w_mk": 0.2}).passed

    def test_fail_above(self):
        assert not _get("KFW-BEG-03").evaluate({"waermebruecken_w_mk": 0.25}).passed


# ── TA Lärm ───────────────────────────────────────────────────────────────

class TestTALaermMischgebiet:
    def test_pass_exact(self):
        assert _get("TALARM-01").evaluate({"mischgebiet_db": 55.0}).passed

    def test_fail_above(self):
        assert not _get("TALARM-01").evaluate({"mischgebiet_db": 55.1}).passed


class TestTALaermWohngebietNacht:
    def test_pass_exact(self):
        assert _get("TALARM-02").evaluate({"wohngebiet_nacht_db": 35.0}).passed

    def test_fail_above(self):
        assert not _get("TALARM-02").evaluate({"wohngebiet_nacht_db": 35.1}).passed


# ── VDI 4645 ──────────────────────────────────────────────────────────────

class TestVDI4645Wandabstand:
    def test_pass_exact(self):
        assert _get("VDI-4645-01").evaluate({"wandabstand_m": 0.5}).passed

    def test_pass_above(self):
        assert _get("VDI-4645-01").evaluate({"wandabstand_m": 1.0}).passed

    def test_fail_below(self):
        assert not _get("VDI-4645-01").evaluate({"wandabstand_m": 0.49}).passed


class TestVDI4645Oeffnungsabstand:
    def test_pass_exact(self):
        assert _get("VDI-4645-02").evaluate({"oeffnungsabstand_m": 2.0}).passed

    def test_pass_above(self):
        assert _get("VDI-4645-02").evaluate({"oeffnungsabstand_m": 3.5}).passed

    def test_fail_below(self):
        assert not _get("VDI-4645-02").evaluate({"oeffnungsabstand_m": 1.99}).passed


# ── Reporter ──────────────────────────────────────────────────────────────

def test_report_json_structure():
    import json
    from cognitum.cna.reporter import report_json

    all_pass_params = {
        "abstand_m": 3.5, "tagpegel_db": 47.0, "nachtpegel_db": 33.0,
        "jaz": 3.8, "dokumentation_vollstaendig": True,
        "vorlauftemp_c": 50.0, "heizstab_prozent": 2.0, "waermebruecken_w_mk": 0.15,
        "mischgebiet_db": 52.0, "wohngebiet_nacht_db": 32.0,
        "wandabstand_m": 0.8, "oeffnungsabstand_m": 2.5,
    }
    results = [r.evaluate(all_pass_params) for r in RULES]
    data = json.loads(report_json(results))

    assert "summary" in data
    assert "detail" in data
    assert "sources" in data
    assert "confidence" in data
    assert len(data["detail"]) == 12
    assert isinstance(data["sources"], list)
    assert 0.0 <= data["confidence"] <= 1.0


def test_report_markdown_contains_table():
    from cognitum.cna.reporter import report_markdown

    results = [r.evaluate({"abstand_m": 2.0}) for r in RULES]
    md = report_markdown(results)
    assert "| GEG-71-01 |" in md
    assert "❌ FAIL" in md
