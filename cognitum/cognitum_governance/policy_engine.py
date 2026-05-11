from cognitum.cna.rules import RULES
from typing import Dict, List, Tuple, Any

class PolicyEngine:
    """Engine that validates outputs against cognitive norm rules."""
    
    def __init__(self):
        """Initialize the policy engine with all norm rules."""
        self.rules = RULES
    
    def check(self, output: dict) -> dict:
        """
        Check output against all norm rules and return compliance status.
        
        Args:
            output: Dictionary containing the output to validate
            
        Returns:
            Dictionary with:
            - compliance_passed: bool indicating if all rules passed
            - violations: list of rule violation descriptions
            - confidence: overall confidence score (0.0-1.0)
        """
        violations = []
        confidences = []
        
        for rule in self.rules:
            try:
                result = rule.check(output)
                if not result.passed:
                    violations.append(result.violation)
                confidences.append(result.confidence)
            except Exception as e:
                violations.append(f"Rule {rule.name} failed with error: {str(e)}")
                confidences.append(0.0)
        
        # Calculate overall confidence (average of all rule confidences)
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Set unverified flag if confidence below threshold
        if overall_confidence < 0.8:
            for i, violation in enumerate(violations):
                if not violation.startswith("[Unverified]"):
                    violations[i] = f"[Unverified] {violation}"
        
        return {
            "compliance_passed": len(violations) == 0,
            "violations": violations,
            "confidence": overall_confidence
        }