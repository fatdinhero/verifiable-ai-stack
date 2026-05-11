"""
gateway/main.py — Privacy-aware LLM gateway (LiteLLM + Presidio).

Exposes an OpenAI-compatible /v1/chat/completions endpoint that:
  1. Anonymizes PII in the incoming messages (Presidio).
  2. Forwards to the configured backend via LiteLLM (default: local Ollama).
  3. Deanonymizes the response before returning it to the caller.

Start:
    uvicorn gateway.main:app --port 8222

No cloud dependency — all traffic stays on localhost by default.
"""

from __future__ import annotations

import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gateway.litellm_proxy import complete, DEFAULT_MODEL
from gateway.presidio_filter import anonymize, deanonymize

app = FastAPI(
    title="COGNITUM LLM Gateway",
    description="Privacy-aware LiteLLM + Presidio proxy — Local-First",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[Message]
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    anonymize_pii: bool = True   # set False only for fully trusted local callers


class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Usage


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "gateway": "cognitum-llm-gateway", "version": "0.1.0"}


@app.post("/v1/chat/completions", response_model=ChatResponse)
def chat_completions(req: ChatRequest) -> ChatResponse:
    # 1. Anonymize PII in every user/system message.
    pii_mappings: list[dict] = []
    clean_messages: list[dict] = []
    for msg in req.messages:
        if req.anonymize_pii and msg.role in ("user", "system"):
            clean_content, mapping = anonymize(msg.content)
            pii_mappings.append(mapping)
        else:
            clean_content, mapping = msg.content, {}
            pii_mappings.append({})
        clean_messages.append({"role": msg.role, "content": clean_content})

    # 2. Forward to LLM backend.
    try:
        raw_reply = complete(
            messages=clean_messages,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM backend error: {exc}") from exc

    # 3. Deanonymize the reply using the merged mapping.
    merged_mapping: dict = {}
    for m in pii_mappings:
        merged_mapping.update(m)
    reply = deanonymize(raw_reply, merged_mapping)

    return ChatResponse(
        model=req.model,
        choices=[Choice(message=Message(role="assistant", content=reply))],
        usage=Usage(),
    )
