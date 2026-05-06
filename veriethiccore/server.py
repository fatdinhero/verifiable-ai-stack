"""
veriethiccore/server.py — EU AI Act compliance MCP server (FastMCP).

5 tools:
  check_prohibited_practices    Art. 5 — prohibited AI practices
  classify_risk_level           Art. 6 / Annex III — risk classification
  check_transparency_obligations Art. 50 — transparency requirements
  check_hleg_trustworthy_ai     HLEG 28-point trustworthy AI checklist
  generate_full_compliance_report Complete report with SHA-256 audit hash

Run:
    python -m veriethiccore.server
    mcp dev veriethiccore/server.py
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastmcp import FastMCP

from veriethiccore.eu_ai_act_rules import (
    check_prohibited_practices as _check_prohibited,
    classify_risk_level as _classify_risk,
    check_transparency_obligations as _check_transparency,
    check_hleg_trustworthy_ai as _check_hleg,
    generate_full_compliance_report as _full_report,
)

mcp = FastMCP(
    "veriethiccore",
    instructions=(
        "EU AI Act (2024/1689) + HLEG Trustworthy AI compliance tools. "
        "Start with classify_risk_level, then run article-specific checks, "
        "or call generate_full_compliance_report for a complete audit with SHA-256 fingerprint."
    ),
)


@mcp.tool()
def check_prohibited_practices(system_description: str) -> Dict[str, Any]:
    """Art. 5 — Check if the system matches any EU AI Act prohibited practice.

    Args:
        system_description: Plain-text description of the AI system's purpose and capabilities.

    Returns a dict with 'prohibited' (bool), 'violations' list, and per-pattern rationale.
    """
    return _check_prohibited(system_description)


@mcp.tool()
def classify_risk_level(
    system_description: str,
    domain: str,
    processes_biometrics: bool = False,
    is_safety_component: bool = False,
) -> Dict[str, str]:
    """Art. 6 / Annex III — Classify the AI system's risk level.

    Args:
        system_description: What the system does.
        domain: Application domain (e.g. 'health', 'employment', 'general').
        processes_biometrics: True if the system processes biometric data.
        is_safety_component: True if the system is a safety component of a regulated product.

    Returns risk_level: prohibited | high | limited | minimal, with rationale.
    """
    return _classify_risk(system_description, domain, processes_biometrics, is_safety_component)


@mcp.tool()
def check_transparency_obligations(
    discloses_ai_nature: bool,
    uses_emotion_recognition: bool = False,
    discloses_emotion_recognition: bool = False,
    generates_synthetic_content: bool = False,
    labels_synthetic_content: bool = False,
) -> Dict[str, Any]:
    """Art. 50 — Check transparency obligations for limited-risk AI systems.

    Args:
        discloses_ai_nature: System informs users they interact with AI.
        uses_emotion_recognition: System performs emotion recognition.
        discloses_emotion_recognition: System discloses emotion recognition to subjects.
        generates_synthetic_content: System produces AI-generated/synthetic content.
        labels_synthetic_content: Generated content is labelled as AI-produced.

    Returns compliance status, findings, and recommendations.
    """
    return _check_transparency(
        discloses_ai_nature,
        discloses_emotion_recognition,
        labels_synthetic_content,
        uses_emotion_recognition,
        generates_synthetic_content,
    )


@mcp.tool()
def check_hleg_trustworthy_ai(completed_criteria: List[str]) -> Dict[str, Any]:
    """HLEG Trustworthy AI — 28-point checklist (Ethics Guidelines, Apr 2019).

    Args:
        completed_criteria: List of satisfied criterion IDs from the 28-point checklist.
            IDs follow the pattern "1.1", "2.3", "4.7" etc.
            Call this tool with an empty list to see all 28 criteria.

    Returns score (0–1), level (trustworthy/developing/insufficient), and per-criterion status.
    """
    return _check_hleg(completed_criteria)


@mcp.tool()
def generate_full_compliance_report(
    system_name: str,
    answers: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a full EU AI Act + HLEG compliance report with SHA-256 audit fingerprint.

    Args:
        system_name: Human-readable name of the AI system.
        answers: Flat dict with system properties. Supported keys:
            system_description (str), domain (str),
            processes_biometrics (bool), is_safety_component (bool),
            discloses_ai_nature (bool), uses_emotion_recognition (bool),
            discloses_emotion_recognition (bool),
            generates_synthetic_content (bool), labels_synthetic_content (bool),
            completed_hleg_criteria (list[str]).

    Returns a consolidated report dict including overall_compliant (bool) and sha256 hash.
    """
    return _full_report(system_name, answers)


if __name__ == "__main__":
    mcp.run()
