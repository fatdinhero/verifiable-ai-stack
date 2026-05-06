"""
litellm_proxy.py — LiteLLM completion wrapper with Local-First routing.

Default backend: Ollama (http://localhost:11434) — no cloud dependency.
LiteLLM is optional; falls back to direct Ollama HTTP when not installed.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional


# LiteLLM is preferred when available.
try:
    import litellm  # type: ignore

    _LITELLM_AVAILABLE = True
except ImportError:
    _LITELLM_AVAILABLE = False


OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "ollama/qwen2.5:7b"  # LiteLLM format; strip prefix for raw HTTP


def _ollama_chat(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: Optional[int],
) -> str:
    """Direct Ollama HTTP fallback (no LiteLLM dependency)."""
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": False,
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["message"]["content"].strip()


def complete(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """Send *messages* to *model* and return the assistant reply as a string.

    Routing priority:
    1. LiteLLM (when installed) — supports Ollama, OpenAI-compat, and more.
    2. Direct Ollama HTTP — always available for local models.
    """
    if _LITELLM_AVAILABLE:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        resp = litellm.completion(**kwargs)
        return resp.choices[0].message.content.strip()

    # Fallback: strip provider prefix for raw Ollama call.
    raw_model = model.split("/", 1)[-1] if "/" in model else model
    return _ollama_chat(raw_model, messages, temperature, max_tokens)
