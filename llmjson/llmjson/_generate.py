from __future__ import annotations

import json as _json
from dataclasses import dataclass
from typing import Optional

import numpy as np

from llmjson._json_context import JSONContextTracker
from llmjson._token_mapper import TokenMapper
from llmjson._vocab_scanner import ANDGate, get_or_build_mapper


@dataclass
class GenerationResult:
    text: str
    token_ids: list[int]
    is_valid: bool
    steps: int
    violations: int


class KVCacheSession:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self._cache = None
        self._generated_ids: list[int] = []
        self._prefilled = False

    def prefill(self, prompt: str) -> np.ndarray:
        import mlx.core as mx
        from mlx_lm.models.cache import make_prompt_cache
        input_ids = self.tokenizer.encode(prompt, return_tensors=None)
        self._cache = make_prompt_cache(self.model)
        logits_mx = self.model(mx.array([input_ids]), cache=self._cache)[0, -1, :]
        mx.eval(logits_mx)
        for lc in self._cache:
            if hasattr(lc, 'keys') and lc.keys is not None: mx.eval(lc.keys)
            if hasattr(lc, 'values') and lc.values is not None: mx.eval(lc.values)
        return np.array(logits_mx.tolist(), dtype=np.float32)

    def advance(self, token_id: int) -> np.ndarray:
        import mlx.core as mx
        self._generated_ids.append(token_id)
        logits_mx = self.model(mx.array([[token_id]]), cache=self._cache)[0, -1, :]
        mx.eval(logits_mx)
        return np.array(logits_mx.tolist(), dtype=np.float32)

    def generated_text(self) -> str:
        return self.tokenizer.decode(self._generated_ids, skip_special_tokens=True)

    def generated_ids(self) -> list[int]:
        return list(self._generated_ids)

    def steps(self) -> int:
        return len(self._generated_ids)


def _build_prompt(tokenizer, prompt: str, schema: dict) -> str:
    schema_str = _json.dumps(schema)
    system_msg = f"Output ONLY valid JSON. No explanation. No markdown. Schema:\n{schema_str}"

    if hasattr(tokenizer, 'apply_chat_template'):
        try:
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ]
            result = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            if result:
                return result
        except Exception:
            pass

    return (
        f"<|im_start|>system\n{system_msg}<|im_end|>\n"
        f"<|im_start|>user\n{prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def generate_json(
    prompt: str,
    schema: dict,
    model,
    tokenizer,
    max_tokens: int = 400,
    verbose: bool = False,
) -> GenerationResult:
    full_prompt = _build_prompt(tokenizer, prompt, schema)

    mapper = get_or_build_mapper(tokenizer, verbose=verbose)
    ctx = JSONContextTracker(schema)
    session = KVCacheSession(model, tokenizer)
    logits = session.prefill(full_prompt)

    actual_vocab_size = len(logits)
    and_gate = ANDGate(mapper, actual_vocab_size)

    violations = 0

    for step in range(max_tokens):
        if ctx.is_complete():
            break

        valid_types = ctx.get_valid_types()

        if verbose:
            dbg = ctx.debug()
            print(f"Step {step:3d}: {dbg['top_state']!s:20s} key={dbg['top_key']!s:15s} "
                  f"valid={[t.name for t in valid_types]}")

        gated = and_gate.apply(logits, valid_types, mode="hard")

        if not np.any(np.isfinite(gated)):
            gated = and_gate.apply(logits, valid_types, mode="soft")
            violations += 1

        token_id = int(np.argmax(gated))

        if token_id == tokenizer.eos_token_id:
            break

        decoded = tokenizer.decode([token_id])
        ctx.update(decoded)

        if verbose:
            print(f"         → token={token_id:6d}  decoded={decoded!r}")

        logits = session.advance(token_id)

    text = session.generated_text()
    try:
        _, end = _json.JSONDecoder().raw_decode(text.strip())
        text = text.strip()[:end]
    except Exception:
        pass

    return GenerationResult(
        text=text,
        token_ids=session.generated_ids(),
        is_valid=ctx.is_complete(),
        steps=session.steps(),
        violations=violations,
    )
