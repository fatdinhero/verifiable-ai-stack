import pytest
from unittest.mock import MagicMock, patch
from cognitum_governance.policy_engine import PolicyEngine


class TestPolicyEngineInit:
    def test_init_loads_rules(self, monkeypatch):
        mock_rules = [MagicMock(), MagicMock()]
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", mock_rules)
        
        engine = PolicyEngine()
        assert engine.rules is mock_rules


class TestPolicyEngineCheck:
    def setup_method(self):
        self.engine = PolicyEngine()
    
    def _create_mock_rule(self, name, passed=True, violation="test violation", confidence=0.9):
        mock_rule = MagicMock()
        mock_rule.name = name
        mock_result = MagicMock()
        mock_result.passed = passed
        mock_result.violation = violation
        mock_result.confidence = confidence
        mock_rule.check.return_value = mock_result
        return mock_rule
    
    def test_check_all_rules_pass(self, monkeypatch):
        rule1 = self._create_mock_rule("rule1", passed=True, confidence=0.9)
        rule2 = self._create_mock_rule("rule2", passed=True, confidence=0.8)
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [rule1, rule2])
        
        engine = PolicyEngine()
        output = {"test": "data"}
        result = engine.check(output)
        
        assert result["compliance_passed"] is True
        assert result["violations"] == []
        assert result["confidence"] == 0.85
    
    def test_check_some_rules_fail(self, monkeypatch):
        rule1 = self._create_mock_rule("rule1", passed=False, violation="violation1", confidence=0.7)
        rule2 = self._create_mock_rule("rule2", passed=True, confidence=0.9)
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [rule1, rule2])
        
        engine = PolicyEngine()
        output = {"test": "data"}
        result = engine.check(output)
        
        assert result["compliance_passed"] is False
        assert len(result["violations"]) == 1
        assert "violation1" in result["violations"][0]
        assert result["confidence"] == 0.8
    
    def test_check_confidence_below_threshold_adds_unverified(self, monkeypatch):
        rule1 = self._create_mock_rule("rule1", passed=False, violation="violation1", confidence=0.6)
        rule2 = self._create_mock_rule("rule2", passed=True, confidence=0.7)
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [rule1, rule2])
        
        engine = PolicyEngine()
        output = {"test": "data"}
        result = engine.check(output)
        
        assert result["compliance_passed"] is False
        for violation in result["violations"]:
            assert violation.startswith("[Unverified]")
    
    def test_check_rule_exception(self, monkeypatch):
        rule1 = self._create_mock_rule("rule1")
        rule1.check.side_effect = Exception("Test error")
        rule2 = self._create_mock_rule("rule2", passed=True, confidence=0.9)
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [rule1, rule2])
        
        engine = PolicyEngine()
        output = {"test": "data"}
        result = engine.check(output)
        
        assert result["compliance_passed"] is False
        assert any("Rule rule1 failed with error: Test error" in v for v in result["violations"])
        assert result["confidence"] == 0.45
    
    def test_check_no_rules(self, monkeypatch):
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [])
        
        engine = PolicyEngine()
        output = {"test": "data"}
        result = engine.check(output)
        
        assert result["compliance_passed"] is True
        assert result["violations"] == []
        assert result["confidence"] == 0.0
    
    def test_check_empty_output(self, monkeypatch):
        rule = self._create_mock_rule("rule1", passed=True, confidence=1.0)
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [rule])
        
        engine = PolicyEngine()
        result = engine.check({})
        
        assert result["compliance_passed"] is True
        assert result["violations"] == []
        assert result["confidence"] == 1.0


class TestPolicyEngineIntegration:
    def test_check_with_real_rules_structure(self, monkeypatch):
        """Test that the engine works with rules that have the expected interface."""
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        mock_result = MagicMock()
        mock_result.passed = True
        mock_result.violation = ""
        mock_result.confidence = 0.95
        mock_rule.check.return_value = mock_result
        
        monkeypatch.setattr("cognitum_governance.policy_engine.RULES", [mock_rule])
        
        engine = PolicyEngine()
        result = engine.check({"content": "test"})
        
        assert result["compliance_passed"] is True
        assert result["confidence"] == 0.95
        mock_rule.check.assert_called_once_with({"content": "test"})