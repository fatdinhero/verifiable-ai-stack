"""
act_checker.py — EU AI Act (2024/1689) compliance checks.

Implements Article-level checks relevant to a wearable/health AI system
like DaySensOS. Stateless functions — no side effects, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    PROHIBITED = "prohibited"          # Annex I + Art. 5
    HIGH = "high"                      # Annex III
    LIMITED = "limited"                # Art. 50 transparency obligations
    MINIMAL = "minimal"                # All other systems


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class CheckResult:
    article: str
    title: str
    status: ComplianceStatus
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ConformityReport:
    system_name: str
    risk_level: RiskLevel
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def overall_status(self) -> ComplianceStatus:
        statuses = {c.status for c in self.checks}
        if ComplianceStatus.NON_COMPLIANT in statuses:
            return ComplianceStatus.NON_COMPLIANT
        if ComplianceStatus.NEEDS_REVIEW in statuses:
            return ComplianceStatus.NEEDS_REVIEW
        return ComplianceStatus.COMPLIANT


# ── Risk classification ───────────────────────────────────────────────────────

_PROHIBITED_KEYWORDS = [
    "social scoring", "real-time biometric", "subliminal manipulation",
    "exploit vulnerabilities", "emotion recognition workplace",
]

_HIGH_RISK_DOMAINS = [
    "health", "medical", "biometric identification", "employment",
    "education", "critical infrastructure", "law enforcement",
    "migration", "justice",
]


def classify_risk(
    system_description: str,
    domain: str,
    processes_biometrics: bool = False,
    is_safety_component: bool = False,
) -> RiskLevel:
    """Classify an AI system's risk level per EU AI Act Annex I/III."""
    desc_lower = system_description.lower()
    domain_lower = domain.lower()

    # Annex I — prohibited practices (Art. 5)
    if any(kw in desc_lower for kw in _PROHIBITED_KEYWORDS):
        return RiskLevel.PROHIBITED

    # Annex III — high-risk systems
    if is_safety_component:
        return RiskLevel.HIGH
    if any(d in domain_lower for d in _HIGH_RISK_DOMAINS):
        return RiskLevel.HIGH
    if processes_biometrics:
        return RiskLevel.HIGH

    # Art. 50 — transparency obligations (chatbots, emotion recognition, deep fakes)
    if "chatbot" in desc_lower or "emotion" in desc_lower or "deepfake" in desc_lower:
        return RiskLevel.LIMITED

    return RiskLevel.MINIMAL


# ── Article-level checks ──────────────────────────────────────────────────────

def check_article_9(risk_management_system_present: bool, has_residual_risk_docs: bool) -> CheckResult:
    """Art. 9 — Risk management system (mandatory for high-risk)."""
    findings, recs = [], []
    if not risk_management_system_present:
        findings.append("No risk management system documented.")
        recs.append("Implement a continuous risk management system (Art. 9 §2).")
    if not has_residual_risk_docs:
        findings.append("Residual risks not documented.")
        recs.append("Document all residual risks after mitigation measures.")
    status = ComplianceStatus.COMPLIANT if not findings else ComplianceStatus.NON_COMPLIANT
    return CheckResult("Art. 9", "Risk Management System", status, findings, recs)


def check_article_10(
    data_governance_policy: bool,
    training_data_documented: bool,
    bias_assessment_done: bool,
) -> CheckResult:
    """Art. 10 — Data and data governance."""
    findings, recs = [], []
    if not data_governance_policy:
        findings.append("No data governance policy.")
        recs.append("Define data governance covering collection, labelling, and quality.")
    if not training_data_documented:
        findings.append("Training data provenance not documented.")
        recs.append("Document data sources, preprocessing, and selection criteria.")
    if not bias_assessment_done:
        findings.append("Bias assessment not completed.")
        recs.append("Conduct bias/fairness assessment on training and test sets.")
    status = ComplianceStatus.COMPLIANT if not findings else ComplianceStatus.NEEDS_REVIEW
    return CheckResult("Art. 10", "Data Governance", status, findings, recs)


def check_article_13(
    system_card_present: bool,
    capabilities_documented: bool,
    limitations_documented: bool,
) -> CheckResult:
    """Art. 13 — Transparency and provision of information."""
    findings, recs = [], []
    if not system_card_present:
        findings.append("No system card / model card available.")
        recs.append("Publish a system card per Art. 13 §3.")
    if not capabilities_documented:
        findings.append("Capabilities not sufficiently documented.")
        recs.append("Document intended purpose, performance levels, and known capabilities.")
    if not limitations_documented:
        findings.append("Limitations and failure modes not documented.")
        recs.append("Add explicit limitations section to technical documentation.")
    status = ComplianceStatus.COMPLIANT if not findings else ComplianceStatus.NON_COMPLIANT
    return CheckResult("Art. 13", "Transparency", status, findings, recs)


def check_article_14(
    human_oversight_measures: List[str],
    override_mechanism_present: bool,
    halt_mechanism_present: bool,
) -> CheckResult:
    """Art. 14 — Human oversight (morphological gate requirement)."""
    findings, recs = [], []
    if not human_oversight_measures:
        findings.append("No human oversight measures defined.")
        recs.append("Define human-in-the-loop checkpoints (morphological gate, VDI 2221).")
    if not override_mechanism_present:
        findings.append("No human override mechanism.")
        recs.append("Implement an override/intervention control accessible to operators.")
    if not halt_mechanism_present:
        findings.append("No system halt / stop mechanism.")
        recs.append("Implement a reliable halt capability for operators.")
    status = ComplianceStatus.COMPLIANT if not findings else ComplianceStatus.NON_COMPLIANT
    return CheckResult("Art. 14", "Human Oversight", status, findings, recs)


def check_article_52(
    discloses_ai_interaction: bool,
    discloses_emotion_recognition: bool,
    discloses_deep_synthesis: bool,
) -> CheckResult:
    """Art. 52 — Transparency obligations for limited-risk systems."""
    findings, recs = [], []
    if not discloses_ai_interaction:
        findings.append("System does not inform users they are interacting with AI.")
        recs.append("Add AI-interaction disclosure at session start (Art. 52 §1).")
    if not discloses_emotion_recognition:
        findings.append("Emotion recognition not disclosed to subjects.")
        recs.append("Inform individuals when emotion recognition is active (Art. 52 §2).")
    if not discloses_deep_synthesis:
        findings.append("Deep synthetic content not labelled.")
        recs.append("Label AI-generated/synthetic content (Art. 52 §3).")
    if not any([not discloses_ai_interaction, not discloses_emotion_recognition,
                not discloses_deep_synthesis]):
        status = ComplianceStatus.COMPLIANT
    else:
        status = ComplianceStatus.NON_COMPLIANT
    return CheckResult("Art. 52", "Transparency Obligations (Limited Risk)", status, findings, recs)


# ── Full conformity assessment ────────────────────────────────────────────────

def full_assessment(system_name: str, answers: dict) -> ConformityReport:
    """Run a full conformity assessment from a flat answers dict.

    Expected keys (all bool unless noted):
        domain (str), system_description (str), processes_biometrics,
        is_safety_component, risk_management_system_present,
        has_residual_risk_docs, data_governance_policy,
        training_data_documented, bias_assessment_done,
        system_card_present, capabilities_documented, limitations_documented,
        human_oversight_measures (list[str]), override_mechanism_present,
        halt_mechanism_present, discloses_ai_interaction,
        discloses_emotion_recognition, discloses_deep_synthesis.
    """
    risk = classify_risk(
        system_description=answers.get("system_description", ""),
        domain=answers.get("domain", ""),
        processes_biometrics=answers.get("processes_biometrics", False),
        is_safety_component=answers.get("is_safety_component", False),
    )
    report = ConformityReport(system_name=system_name, risk_level=risk)

    if risk in (RiskLevel.HIGH, RiskLevel.PROHIBITED):
        report.checks.append(check_article_9(
            answers.get("risk_management_system_present", False),
            answers.get("has_residual_risk_docs", False),
        ))
        report.checks.append(check_article_10(
            answers.get("data_governance_policy", False),
            answers.get("training_data_documented", False),
            answers.get("bias_assessment_done", False),
        ))
        report.checks.append(check_article_13(
            answers.get("system_card_present", False),
            answers.get("capabilities_documented", False),
            answers.get("limitations_documented", False),
        ))
        report.checks.append(check_article_14(
            answers.get("human_oversight_measures", []),
            answers.get("override_mechanism_present", False),
            answers.get("halt_mechanism_present", False),
        ))

    if risk == RiskLevel.LIMITED:
        report.checks.append(check_article_52(
            answers.get("discloses_ai_interaction", False),
            answers.get("discloses_emotion_recognition", False),
            answers.get("discloses_deep_synthesis", False),
        ))

    return report
