#!/usr/bin/env python3
"""
governance/data_routing.py
IP-sensitiver LLM-Router: MIMO (extern) vs. Ollama (lokal)
Verhindert dass unveröffentlichtes IP, Chat-History oder persönliche Daten
an externe APIs gesendet werden.
"""
from __future__ import annotations

# ─── ROUTING-POLICIES ────────────────────────────────────────────────────────

SAFE_FOR_MIMO = [
    "SPALTEN Agent Phasen S,P,A,L,T,E,N",
    "Allgemeine Engineering-Probleme",
    "Öffentlich publizierte Papers (Zenodo DOIs)",
    "Cases die bereits OTS-gestempelt sind",
]

ONLY_OLLAMA_LOCAL = [
    "cognitum_chat_history ChromaDB",
    "MetaBell Formeln unveröffentlicht",
    "COS-Formel Details",
    "VeriEthicCore intern",
    "Alle unveröffentlichten IP-Konzepte",
    "Persönliche Daten",
    "Saskia / Treuhand Details",
]

# Keywords die eine lokale Verarbeitung erzwingen
_SENSITIVE_KEYWORDS = [
    "metabell",
    "cos-formel",
    "veriethiccore intern",
    "saskia",
    "treuhand",
    "insolvenz",
    "unveröffentlicht",
    "chat_history",
    "persönlich",
    "operator_psi",   # alias für metabell
    "bound_t",        # alias für tsirelson
    "score_w",        # alias für wisescore
    "metric_q",       # alias für dqm
]


def get_router(content: str) -> str:
    """
    Gibt 'mimo' oder 'ollama' zurück basierend auf Content-Klassifizierung.
    Sicher-Default: bei Zweifel → 'ollama'.
    """
    lower = content.lower()
    for kw in _SENSITIVE_KEYWORDS:
        if kw in lower:
            return "ollama"
    return "mimo"


# ─── LLM-BACKEND URLS ────────────────────────────────────────────────────────

MIMO_BASE_URL  = "https://api.xiaomimimo.com/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MIMO_MODEL     = "mimo-v2.5-pro"
OLLAMA_MODEL   = "qwen2.5:7b"
