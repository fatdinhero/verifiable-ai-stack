"""Embedding sidecar — ONNX Runtime backend.

Uses all-MiniLM-L6-v2 (quantized, 22MB) via onnxruntime + tokenizers.
No torch, no sentence-transformers, no internet access at runtime.

Endpoints:
    POST /embed  {"texts": ["...", "..."]}  ->  {"embeddings": [[...], [...]]}
    GET  /health
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import List

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="AgentsProtocol Embed Service", version="2.0")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/app/model"))

_session = None
_tokenizer = None


def _load() -> None:
    global _session, _tokenizer
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        _session = ort.InferenceSession(
            str(MODEL_DIR / "model.onnx"),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
        _tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
        _tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=128)
        _tokenizer.enable_truncation(max_length=128)
        logger.info("ONNX model loaded from %s", MODEL_DIR)
    except Exception as exc:
        logger.warning("Could not load ONNX model (%s) — using stub", exc)


@app.on_event("startup")
async def startup() -> None:
    _load()


def _mean_pool(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    mask = attention_mask[..., np.newaxis].astype(float)
    summed = (token_embeddings * mask).sum(axis=1)
    counts = mask.sum(axis=1).clip(min=1e-9)
    pooled = summed / counts
    norms = np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-9)
    return (pooled / norms).astype(np.float32)


def _stub_embed(text: str) -> List[float]:
    DIM = 384
    digest = hashlib.sha256(text.encode()).digest()
    raw = bytes(digest[i % 32] for i in range(DIM))
    vec = np.array([b - 127.5 for b in raw], dtype=np.float64)
    norm = np.linalg.norm(vec)
    return (vec / norm if norm > 0 else vec).tolist()


def _onnx_embed(texts: List[str]) -> List[List[float]]:
    enc = _tokenizer.encode_batch(texts)
    input_ids = np.array([e.ids for e in enc], dtype=np.int64)
    attention_mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids)

    outputs = _session.run(
        None,
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        },
    )
    # outputs[0] = last_hidden_state (batch, seq, 384)
    pooled = _mean_pool(outputs[0], attention_mask)
    return pooled.tolist()


class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str


@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    if _session is None or _tokenizer is None:
        return EmbedResponse(
            embeddings=[_stub_embed(t) for t in req.texts],
            model="stub",
        )
    return EmbedResponse(
        embeddings=_onnx_embed(req.texts),
        model="all-MiniLM-L6-v2-qint8",
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model_loaded": _session is not None}
