#!/usr/bin/env python3
"""
scripts/rag_chat_history.py
Chat-History RAG für autonomous_loop.py

Läuft NUR lokal via Ollama-Embeddings — niemals chat_history-Inhalte
an externe LLMs (MiMo) senden. data_routing.py-Konform.
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.chat_indexer import search_chats


def query_chat_history(problem: str, n: int = 3) -> str:
    """
    Sucht relevante Chunks in cognitum_chat_history und gibt
    einen Kontext-String zurück, der dem SPALTEN-Problem vorangestellt wird.

    Nur lokale Ollama-Embeddings — kein MiMo-Call.
    Chunks mit dist > 0.5 werden übersprungen (zu weit vom Thema entfernt).
    """
    try:
        results = search_chats(problem, n=n)
        if not results:
            return ""

        snippets = []
        for r in results:
            if r["distance"] > 0.5:
                continue
            meta    = r["metadata"]
            snippet = r["content"][:300].strip()
            if not snippet:
                continue
            platform = meta.get("platform", "?")
            role     = meta.get("role", "?")
            snippets.append(f"[{platform} | {role}]\n{snippet}")

        if not snippets:
            return ""

        context  = "=== Relevante vergangene Entscheidungen ===\n"
        context += "\n\n".join(snippets)
        return context.strip()

    except Exception:
        return ""
