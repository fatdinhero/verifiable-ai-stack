"""Embedding sidecar service.

Provides a single endpoint:
    POST /embed  {"texts": ["...", "..."]}  ->  {"embeddings": [[...], [...]]}

Uses sentence-transformers all-MiniLM-L6-v2 (384-dim, ~90MB).
Falls back to the stub embedder (SHA-256 tiling) if the model is unavailable,
so the validator can start without the model downloaded.

Run:
    pip install -r requirements.txt
    uvicorn embed.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import List

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="AgentsProtocol Embed Service", version="1.0")

# ---------------------------------------------------------------------------
# Model loading — lazy, with stub fallback
# ---------------------------------------------------------------------------

_model = None
_use_stub = False

def _load_model() -> None:
    global _model, _use_stub
    model_name = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(model_name)
        logger.info("Loaded embedding model: %s", model_name)
    except Exception as exc:
        logger.warning("Could not load %s (%s) — using stub embedder", model_name, exc)
        _use_stub = True


@app.on_event("startup")
async def startup() -> None:
    _load_model()


# ---------------------------------------------------------------------------
# Stub embedder (mirrors Rust stub_embed / Python _stub_embed exactly)
# ---------------------------------------------------------------------------

def _stub_embed(text: str) -> List[float]:
    DIM = 384
    digest = hashlib.sha256(text.encode()).digest()
    raw = bytes(digest[i % 32] for i in range(DIM))
    vec = np.array([b - 127.5 for b in raw], dtype=np.float64)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str


@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    if _use_stub or _model is None:
        embeddings = [_stub_embed(t) for t in req.texts]
        return EmbedResponse(embeddings=embeddings, model="stub")

    vecs = _model.encode(req.texts, normalize_embeddings=True)
    return EmbedResponse(
        embeddings=vecs.tolist(),
        model=_model.get_sentence_embedding_dimension() and "all-MiniLM-L6-v2",
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "stub": _use_stub}
