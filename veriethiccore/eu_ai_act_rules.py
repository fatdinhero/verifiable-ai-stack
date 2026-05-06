"""
eu_ai_act_rules.py — Compliance logic for the EU AI Act (2024/1689).

Pure functions — no side effects, no I/O. Called by server.py (FastMCP)
and act_checker.py (full conformity assessment).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Art. 5 — Prohibited practices ────────────────────────────────────────────

_PROHIBITED_PATTERNS = [
    ("subliminal manipulation", "Art. 5(1)(a): subliminal techniques that distort behaviour"),
    ("exploit vulnerabilities", "Art. 5(1)(b): exploiting age/disability vulnerabilities"),
    ("social scoring", "Art. 5(1)(c): social scoring by public authorities"),
    ("real-time biometric", "Art. 5(1)(d): real-time remote biometric ID in public spaces"),
    ("emotion recognition workplace", "Art. 5(1)(f): emotion recognition in workplace/education"),
    ("predictive policing individual", "Art. 5(1)(e): individual crime prediction"),
    ("scrape facial images", "Art. 5(1)(g): facial recognition databases via scraping"),
]


def check_prohibited_practices(system_description: str) -> Dict[str, Any]:
    """Art. 5 — Check whether the system description matches any prohibited AI practice."""
    desc = system_description.lower()
    violations: List[Dict[str, str]] = []
    for pattern, rationale in _PROHIBITED_PATTERNS:
        if pattern in desc:
            violations.append({"pattern": pattern, "rationale": rationale})
    return {
        "article": "Art. 5",
        "title": "Prohibited AI Practices",
        "prohibited": len(violations) > 0,
        "violations": violations,
        "compliant": len(violations) == 0,
    }


# ── Art. 6 — Risk level classification ───────────────────────────────────────

_HIGH_RISK_DOMAINS = [
    "health", "medical", "biometric", "employment", "education",
    "critical infrastructure", "law enforcement", "migration",
    "justice", "financial", "insurance",
]

_LIMITED_RISK_INDICATORS = ["chatbot", "emotion recognition", "deepfake", "synthetic content"]


def classify_risk_level(
    system_description: str,
    domain: str,
    processes_biometrics: bool = False,
    is_safety_component: bool = False,
) -> Dict[str, str]:
    """Art. 6 — Classify AI system risk level: prohibited | high | limited | minimal."""
    desc = system_description.lower()
    dom = domain.lower()

    prohibited = check_prohibited_practices(system_description)
    if prohibited["prohibited"]:
        return {
            "risk_level": "prohibited",
            "rationale": "Matches Art. 5 prohibited practice.",
            "primary_violation": prohibited["violations"][0]["rationale"] if prohibited["violations"] else "",
        }

    if is_safety_component or any(d in dom for d in _HIGH_RISK_DOMAINS) or processes_biometrics:
        return {
            "risk_level": "high",
            "rationale": "Falls under Annex III high-risk categories.",
            "applicable_annex": "Annex III",
        }

    if any(ind in desc for ind in _LIMITED_RISK_INDICATORS):
        return {
            "risk_level": "limited",
            "rationale": "Art. 50 transparency obligations apply.",
            "applicable_article": "Art. 50",
        }

    return {
        "risk_level": "minimal",
        "rationale": "No high-risk or prohibited characteristics detected.",
    }


# ── Art. 50 — Transparency obligations ───────────────────────────────────────

def check_transparency_obligations(
    discloses_ai_nature: bool,
    discloses_emotion_recognition: bool = False,
    labels_synthetic_content: bool = False,
    uses_emotion_recognition: bool = False,
    generates_synthetic_content: bool = False,
) -> Dict[str, Any]:
    """Art. 50 — Check transparency obligations for limited-risk AI systems."""
    findings: List[str] = []
    recommendations: List[str] = []

    if not discloses_ai_nature:
        findings.append("Users not informed they interact with AI (Art. 50 §1).")
        recommendations.append("Add AI-interaction disclosure at session/interaction start.")

    if uses_emotion_recognition and not discloses_emotion_recognition:
        findings.append("Emotion recognition active but not disclosed (Art. 50 §2).")
        recommendations.append("Inform individuals when emotion recognition is in use.")

    if generates_synthetic_content and not labels_synthetic_content:
        findings.append("Synthetic/AI-generated content not labelled (Art. 50 §3).")
        recommendations.append("Mark all AI-generated content with a machine-readable label.")

    return {
        "article": "Art. 50",
        "title": "Transparency Obligations",
        "compliant": len(findings) == 0,
        "findings": findings,
        "recommendations": recommendations,
    }


# ── HLEG — Trustworthy AI (28-point checklist) ───────────────────────────────

_HLEG_CRITERIA = [
    # Pillar 1: Lawful AI
    ("1.1", "Legal basis for processing established"),
    ("1.2", "GDPR compliance verified"),
    ("1.3", "Sector-specific legal requirements met"),
    ("1.4", "Intellectual property rights respected"),
    # Pillar 2: Ethical AI
    ("2.1", "Human agency and oversight preserved"),
    ("2.2", "No deception or manipulation"),
    ("2.3", "Fairness and non-discrimination assured"),
    ("2.4", "Privacy and data governance maintained"),
    ("2.5", "Societal and environmental wellbeing considered"),
    ("2.6", "Accountability and responsibility defined"),
    # Pillar 3: Robust AI
    ("3.1", "Technical robustness and safety tested"),
    ("3.2", "Resilience to attack and security assured"),
    ("3.3", "Fallback plan and fail-safe in place"),
    ("3.4", "Accuracy and reproducibility documented"),
    ("3.5", "Reliability and availability measured"),
    ("3.6", "System performance regularly evaluated"),
    ("3.7", "Explainability and interpretability provided"),
    ("3.8", "Transparency of AI system documented"),
    ("3.9", "Diversity and inclusion by design"),
    ("3.10", "Accessibility for all user groups"),
    ("3.11", "Stakeholder participation in design"),
    # Additional governance
    ("4.1", "Risk management process documented (Art. 9)"),
    ("4.2", "Data governance policy in place (Art. 10)"),
    ("4.3", "Technical documentation prepared (Art. 11)"),
    ("4.4", "Record-keeping / logging implemented (Art. 12)"),
    ("4.5", "Transparency information published (Art. 13)"),
    ("4.6", "Human oversight mechanism operational (Art. 14)"),
    ("4.7", "Conformity assessment completed (Art. 43)"),
]


def check_hleg_trustworthy_ai(completed_criteria: List[str]) -> Dict[str, Any]:
    """HLEG Trustworthy AI — 28-point checklist assessment.

    completed_criteria: list of criterion IDs (e.g. ["1.1", "1.2", "3.1"]) that are satisfied.
    """
    completed_set = set(completed_criteria)
    results = []
    for cid, description in _HLEG_CRITERIA:
        results.append({
            "id": cid,
            "description": description,
            "satisfied": cid in completed_set,
        })
    total = len(_HLEG_CRITERIA)
    satisfied = sum(1 for r in results if r["satisfied"])
    score = satisfied / total
    return {
        "title": "HLEG Trustworthy AI Assessment",
        "total_criteria": total,
        "satisfied": satisfied,
        "score": round(score, 3),
        "level": "trustworthy" if score >= 0.8 else ("developing" if score >= 0.5 else "insufficient"),
        "criteria": results,
    }


# ── Full compliance report ────────────────────────────────────────────────────

def generate_full_compliance_report(system_name: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a complete EU AI Act + HLEG compliance report with SHA-256 fingerprint."""
    prohibited = check_prohibited_practices(answers.get("system_description", ""))
    risk = classify_risk_level(
        answers.get("system_description", ""),
        answers.get("domain", ""),
        answers.get("processes_biometrics", False),
        answers.get("is_safety_component", False),
    )
    transparency = check_transparency_obligations(
        answers.get("discloses_ai_nature", False),
        answers.get("discloses_emotion_recognition", False),
        answers.get("labels_synthetic_content", False),
        answers.get("uses_emotion_recognition", False),
        answers.get("generates_synthetic_content", False),
    )
    hleg = check_hleg_trustworthy_ai(answers.get("completed_hleg_criteria", []))

    report: Dict[str, Any] = {
        "system_name": system_name,
        "risk_level": risk["risk_level"],
        "prohibited_check": prohibited,
        "risk_classification": risk,
        "transparency_check": transparency,
        "hleg_assessment": hleg,
        "overall_compliant": (
            not prohibited["prohibited"]
            and transparency["compliant"]
            and hleg["score"] >= 0.5
        ),
    }

    # SHA-256 fingerprint for audit trail.
    fingerprint_input = json.dumps(
        {k: v for k, v in report.items() if k != "sha256"}, sort_keys=True
    ).encode()
    report["sha256"] = hashlib.sha256(fingerprint_input).hexdigest()
    return report
