"""
governance/problem_generator.py
ProblemGenerator — konvertiert echte Signale in SPALTEN-Engineering-Probleme
Echte Signale priorisiert, LLM-generierte nur als Fallback.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.signal_sources import RealSignalFetcher, _llm_call

URGENCY_VALUES = {"low", "medium", "high", "critical"}


def _signal_to_problem(signal: dict) -> dict:
    """Konvertiert ein Signal via LLM in ein strukturiertes Engineering-Problem."""
    title = signal.get("title", "")
    body = signal.get(
        "problem",
        signal.get("description", signal.get("body", ""))
    )
    source = signal.get("source", "unknown")
    domain = signal.get("domain", "engineering")

    prompt = (
        f"Signal aus Quelle '{source}':\n"
        f"Titel: {title}\n"
        f"Details: {str(body)[:400]}\n\n"
        "Konvertiere diesen Issue/Signal in ein praezises Engineering-Problem "
        "fuer SPALTEN-Analyse (COGNITUM/DaySensOS). "
        'Antworte NUR mit validem JSON: '
        '{"problem": "...", "domain": "...", "urgency": "medium"}'
    )

    response = _llm_call(prompt, timeout=90)

    # JSON aus LLM-Antwort extrahieren
    parsed = None
    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
        except json.JSONDecodeError:
            pass

    if parsed:
        urgency = parsed.get("urgency", "medium")
        if urgency not in URGENCY_VALUES:
            urgency = "medium"
        return {
            "problem": parsed.get("problem") or title or body[:100],
            "domain":  parsed.get("domain")  or domain,
            "urgency": urgency,
            "source":  source,
            "raw_signal": signal,
        }

    # Fallback: kein gueltiges JSON
    raw_problem = f"{title}: {str(body)[:100]}" if title else str(body)[:150]
    return {
        "problem": raw_problem.strip() or "Unbekanntes Problem",
        "domain":  domain,
        "urgency": "medium",
        "source":  source,
        "raw_signal": signal,
    }


def _generate_llm_problem(index: int) -> dict:
    """Generiert ein LLM-synthetisches Engineering-Problem als Fallback."""
    prompt = (
        f"Generiere Engineering-Problem #{index} fuer COGNITUM/DaySensOS "
        "(Privacy-First Wearable AI OS, VDI 2221, DSGVO). "
        "Sei spezifisch und technisch praeizse. "
        'Antworte NUR mit validem JSON: '
        '{"problem": "...", "domain": "...", "urgency": "medium"}'
    )
    response = _llm_call(prompt, timeout=90)

    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            p = json.loads(m.group())
            urgency = p.get("urgency", "medium")
            if urgency not in URGENCY_VALUES:
                urgency = "medium"
            return {
                "problem": p.get("problem", response[:150]),
                "domain":  p.get("domain", "engineering"),
                "urgency": urgency,
                "source":  "llm_generated",
            }
        except json.JSONDecodeError:
            pass

    return {
        "problem": response[:200] if not response.startswith("[SIMULATION]") else
                   f"COGNITUM Architekturproblem #{index}: Sensor-Consent-Validierung",
        "domain":  "engineering",
        "urgency": "medium",
        "source":  "llm_generated",
    }


class ProblemGenerator:
    def __init__(self):
        self.fetcher = RealSignalFetcher()

    def generate(self, n: int = 5) -> List[dict]:
        """
        Generiert n Engineering-Probleme.
        1. fetch_all() fuer echte Signale
        2. LLM-Fallback fuer fehlende Probleme
        3. Echte Signale werden priorisiert (llm_generated ans Ende)
        """
        # 1. Echte Signale
        signals = self.fetcher.fetch_all(repos=["fatdinhero/cognitum"])
        print(f"  ProblemGenerator: {len(signals)} echte Signale empfangen")

        problems: List[dict] = []

        # 2. Signale in Probleme konvertieren
        for sig in signals[:n]:
            p = _signal_to_problem(sig)
            if p.get("problem"):
                problems.append(p)
            if len(problems) >= n:
                break

        # 3. LLM-Fallback wenn zu wenig echte Signale
        remaining = n - len(problems)
        if remaining > 0:
            print(f"  LLM-Fallback: {remaining} synthetische Probleme")
            for i in range(remaining):
                p = _generate_llm_problem(len(problems) + i + 1)
                problems.append(p)

        # 4. Echte Signale zuerst sortieren
        problems.sort(key=lambda p: (1 if p.get("source") == "llm_generated" else 0))

        return problems[:n]
