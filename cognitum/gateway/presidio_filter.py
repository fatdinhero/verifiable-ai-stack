"""
presidio_filter.py — PII anonymization/deanonymization via Microsoft Presidio.

Falls back to a no-op pass-through when presidio is not installed so the
gateway stays functional in minimal environments (Local-First principle).
"""

from __future__ import annotations

import re
from typing import Dict, Tuple


try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    _analyzer = AnalyzerEngine()
    _anonymizer = AnonymizerEngine()
    _PRESIDIO_AVAILABLE = True
except ImportError:
    _PRESIDIO_AVAILABLE = False


# Entities we anonymize before sending to any LLM backend.
_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
    "IP_ADDRESS", "IBAN_CODE", "CREDIT_CARD", "DATE_TIME",
    "NRP",  # national registration / ID numbers
]


def anonymize(text: str, language: str = "de") -> Tuple[str, Dict[str, str]]:
    """Return (anonymized_text, mapping) where mapping allows deanonymization.

    If Presidio is unavailable the original text is returned unchanged with an
    empty mapping — no PII leaks out because the gateway routes only to local
    Ollama endpoints by default.
    """
    if not _PRESIDIO_AVAILABLE or not text.strip():
        return text, {}

    results = _analyzer.analyze(text=text, language=language, entities=_ENTITIES)
    if not results:
        return text, {}

    # Replace each detected entity with a stable placeholder.
    mapping: Dict[str, str] = {}
    anonymized = text
    # Sort by position descending so replacements don't shift offsets.
    for res in sorted(results, key=lambda r: r.start, reverse=True):
        placeholder = f"<{res.entity_type}_{len(mapping) + 1}>"
        original = text[res.start:res.end]
        mapping[placeholder] = original
        anonymized = anonymized[: res.start] + placeholder + anonymized[res.end :]

    return anonymized, mapping


def deanonymize(text: str, mapping: Dict[str, str]) -> str:
    """Restore original entities in *text* using *mapping* from :func:`anonymize`."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
