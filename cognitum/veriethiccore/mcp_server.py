"""
veriethiccore/mcp_server.py — EU AI Act compliance MCP server.

Exposes COGNITUM governance tools to Claude Code and other MCP clients:
  - classify_risk          classify an AI system's risk level
  - check_article          run a single Article check
  - full_assessment        complete conformity assessment
  - morphological_gate     Art. 14 human-oversight gate (from CLAUDE.md §8)

Run (stdio transport, standard MCP pattern):
    python -m veriethiccore.mcp_server

Or via mcp dev:
    mcp dev veriethiccore/mcp_server.py
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from veriethiccore.act_checker import (
    RiskLevel,
    classify_risk,
    check_article_9,
    check_article_10,
    check_article_13,
    check_article_14,
    check_article_52,
    full_assessment,
    ConformityReport,
    CheckResult,
)

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore

    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


# ── Serialization helpers ─────────────────────────────────────────────────────

def _check_to_dict(c: CheckResult) -> Dict[str, Any]:
    return {
        "article": c.article,
        "title": c.title,
        "status": c.status.value,
        "findings": c.findings,
        "recommendations": c.recommendations,
    }


def _report_to_dict(r: ConformityReport) -> Dict[str, Any]:
    return {
        "system_name": r.system_name,
        "risk_level": r.risk_level.value,
        "overall_status": r.overall_status.value,
        "checks": [_check_to_dict(c) for c in r.checks],
    }


# ── MCP server ────────────────────────────────────────────────────────────────

if _MCP_AVAILABLE:
    mcp = FastMCP("veriethiccore", instructions=(
        "EU AI Act (2024/1689) compliance tools for COGNITUM/DaySensOS. "
        "Use classify_risk first, then run article checks or full_assessment."
    ))

    @mcp.tool()
    def classify_risk_tool(
        system_description: str,
        domain: str,
        processes_biometrics: bool = False,
        is_safety_component: bool = False,
    ) -> Dict[str, str]:
        """Classify an AI system's risk level per EU AI Act Annex I / Annex III.

        Returns risk_level: prohibited | high | limited | minimal
        """
        level = classify_risk(system_description, domain, processes_biometrics, is_safety_component)
        return {"risk_level": level.value, "description": level.name}

    @mcp.tool()
    def check_article_tool(article: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single EU AI Act Article check.

        article: "9" | "10" | "13" | "14" | "52"
        params: article-specific boolean/list parameters (see act_checker.py).
        """
        dispatch = {
            "9":  lambda p: check_article_9(
                p.get("risk_management_system_present", False),
                p.get("has_residual_risk_docs", False),
            ),
            "10": lambda p: check_article_10(
                p.get("data_governance_policy", False),
                p.get("training_data_documented", False),
                p.get("bias_assessment_done", False),
            ),
            "13": lambda p: check_article_13(
                p.get("system_card_present", False),
                p.get("capabilities_documented", False),
                p.get("limitations_documented", False),
            ),
            "14": lambda p: check_article_14(
                p.get("human_oversight_measures", []),
                p.get("override_mechanism_present", False),
                p.get("halt_mechanism_present", False),
            ),
            "52": lambda p: check_article_52(
                p.get("discloses_ai_interaction", False),
                p.get("discloses_emotion_recognition", False),
                p.get("discloses_deep_synthesis", False),
            ),
        }
        fn = dispatch.get(str(article))
        if fn is None:
            return {"error": f"Article '{article}' not implemented. Available: {list(dispatch)}"}
        return _check_to_dict(fn(params))

    @mcp.tool()
    def full_assessment_tool(system_name: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete EU AI Act conformity assessment.

        answers: flat dict with all system properties (see act_checker.full_assessment).
        Returns a ConformityReport with risk_level, overall_status, and per-article checks.
        """
        report = full_assessment(system_name, answers)
        return _report_to_dict(report)

    @mcp.tool()
    def morphological_gate(
        decision_description: str,
        oversight_measures: list[str],
        override_possible: bool,
        halt_possible: bool,
    ) -> Dict[str, Any]:
        """Art. 14 morphological gate — required before every automated decision (CLAUDE.md §8).

        Returns gate_passed: bool and the Article 14 CheckResult.
        """
        result = check_article_14(oversight_measures, override_possible, halt_possible)
        gate_passed = result.status.value == "compliant"
        return {
            "gate_passed": gate_passed,
            "decision": decision_description,
            "check": _check_to_dict(result),
        }

    @mcp.resource("eu_ai_act://articles/summary")
    def articles_summary() -> str:
        """Key EU AI Act articles implemented in veriethiccore."""
        return json.dumps({
            "Art. 5":  "Prohibited AI practices (Annex I)",
            "Art. 9":  "Risk management system — mandatory for high-risk",
            "Art. 10": "Data and data governance — training/validation/test data",
            "Art. 13": "Transparency and provision of information to deployers",
            "Art. 14": "Human oversight — morphological gate (DaySensOS CLAUDE.md §8)",
            "Art. 52": "Transparency obligations for limited-risk (chatbots, emotion AI)",
        }, indent=2)

else:
    # CLI fallback — print a JSON report without MCP overhead.
    def _cli_demo() -> None:
        daysensos_answers = {
            "system_description": "Privacy-first wearable AI OS processing sensor fusion data",
            "domain": "health",
            "processes_biometrics": False,
            "is_safety_component": False,
            "risk_management_system_present": True,
            "has_residual_risk_docs": True,
            "data_governance_policy": True,
            "training_data_documented": True,
            "bias_assessment_done": False,
            "system_card_present": False,
            "capabilities_documented": True,
            "limitations_documented": True,
            "human_oversight_measures": ["morphological gate", "VDI 2221 sign-off"],
            "override_mechanism_present": True,
            "halt_mechanism_present": True,
            "discloses_ai_interaction": True,
            "discloses_emotion_recognition": False,
            "discloses_deep_synthesis": True,
        }
        report = full_assessment("DaySensOS", daysensos_answers)
        print(json.dumps(_report_to_dict(report), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if _MCP_AVAILABLE:
        mcp.run()
    else:
        print(
            "[veriethiccore] mcp package not installed — running CLI demo.\n"
            "Install: pip install mcp\n",
            file=sys.stderr,
        )
        _cli_demo()
