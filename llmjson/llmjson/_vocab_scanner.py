from __future__ import annotations

import hashlib
import json as _json
import os
import re
from pathlib import Path
from typing import Optional

import numpy as np

from llmjson._types import TokenType
from llmjson._token_mapper import TokenMapper


def classify_decoded_token(text: str) -> Optional[TokenType]:
    t = text.lstrip()
    if not t:
        return None

    if t == '{':                      return TokenType.LBRACE
    if t == '}':                      return TokenType.RBRACE
    if t == '[':                      return TokenType.LBRACKET
    if t == ']':                      return TokenType.RBRACKET
    if t in (':', ': ', ' :'):        return TokenType.COLON
    if t in (',', ', ', ' ,'):        return TokenType.COMMA
    if t == '"':                      return TokenType.STRING
    if t == 'true':                   return TokenType.TRUE
    if t == 'false':                  return TokenType.FALSE
    if t == 'null':                   return TokenType.NULL

    if re.fullmatch(r'-?[0-9]+(\.[0-9]*)?([eE][+-]?[0-9]+)?', t):
        return TokenType.NUMBER
    if re.fullmatch(r'[0-9]+', t):
        return TokenType.NUMBER
    if t == '.':
        return TokenType.NUMBER
    if t == '-':
        return TokenType.NUMBER
    if re.fullmatch(r'\.[0-9]+', t):
        return TokenType.NUMBER

    if t.startswith('"'):
        return TokenType.STRING

    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_\- ]*', t):
        return TokenType.STRING_KEY

    if t.startswith('{'):             return TokenType.LBRACE
    if t.startswith('}'):             return TokenType.RBRACE
    if t.startswith('['):             return TokenType.LBRACKET
    if t.startswith(']'):             return TokenType.RBRACKET

    return None


class EmptyMaskError(Exception):
    pass


class VocabScanner:
    def __init__(self):
        self._token_map: Optional[dict[int, TokenType]] = None
        self._scanned = False
        self._vocab_size = 0
        self._coverage = 0

    def scan(self, tokenizer, verbose: bool = False) -> TokenMapper:
        vocab_size = getattr(tokenizer, 'vocab_size', 152064)
        self._vocab_size = vocab_size
        token_map: dict[int, TokenType] = {}

        for token_id in range(vocab_size):
            try:
                decoded = tokenizer.decode([token_id])
                ttype = classify_decoded_token(decoded)
                if ttype is not None:
                    token_map[token_id] = ttype
            except Exception:
                continue

        self._token_map = token_map
        self._coverage = len(token_map)
        self._scanned = True

        if verbose:
            print(f"[VocabScanner] Scanned {vocab_size} tokens")
            print(f"[VocabScanner] JSON-relevant: {self._coverage} ({self._coverage/vocab_size*100:.1f}%)")

        return TokenMapper(token_map)


class ANDGate:
    def __init__(self, token_mapper: TokenMapper, vocab_size: int):
        self._mapper = token_mapper
        self._vocab_size = vocab_size
        self._mask_cache: dict[frozenset, np.ndarray] = {}

    def apply(
        self,
        logits: np.ndarray,
        valid_types: set[TokenType],
        mode: str = "hard",
        soft_penalty: float = -100.0,
    ) -> np.ndarray:
        key = frozenset(valid_types)
        if key not in self._mask_cache:
            mask = np.zeros(self._vocab_size, dtype=bool)
            for tid in self._mapper.valid_ids_for_types(valid_types, self._vocab_size):
                if tid < self._vocab_size:
                    mask[tid] = True
            self._mask_cache[key] = mask

        mask = self._mask_cache[key]
        if not np.any(mask):
            raise EmptyMaskError(
                f"No tokens found for types {[t.name for t in valid_types]}. "
                f"The VocabScanner could not classify any vocabulary token into these types."
            )

        gated = logits.copy()
        if mode == "hard":
            gated[~mask] = -np.inf
        else:
            gated[~mask] += soft_penalty
        return gated


_CACHE_DIR = Path.home() / ".cache" / "llmjson"
_mapper_cache: dict[str, TokenMapper] = {}


def _cache_key(tokenizer) -> str:
    return getattr(tokenizer, "name_or_path", None) or str(
        getattr(tokenizer, "vocab_size", id(tokenizer))
    )


def _disk_cache_path(key: str) -> Path:
    from llmjson import __version__
    safe = hashlib.md5(f"{key}:{__version__}".encode()).hexdigest()
    return _CACHE_DIR / f"{safe}.json"


def _save_to_disk(path: Path, token_map: dict[int, TokenType]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {str(k): v.name for k, v in token_map.items()}
        path.write_text(_json.dumps(data))
    except Exception:
        pass


def _load_from_disk(path: Path) -> Optional[dict[int, TokenType]]:
    try:
        if not path.exists():
            return None
        data = _json.loads(path.read_text())
        type_map = {m.name: m for m in TokenType}
        return {int(k): type_map[v] for k, v in data.items() if v in type_map}
    except Exception:
        return None


def get_or_build_mapper(tokenizer, verbose: bool = True) -> TokenMapper:
    key = _cache_key(tokenizer)
    if key in _mapper_cache:
        return _mapper_cache[key]

    disk_path = _disk_cache_path(key)
    cached = _load_from_disk(disk_path)
    if cached is not None:
        if verbose:
            print(f"[VocabScanner] Loaded cached token map for {key!r}")
        mapper = TokenMapper(cached)
        _mapper_cache[key] = mapper
        return mapper

    if verbose:
        print(f"[VocabScanner] Building token map for {key!r} ...")
    scanner = VocabScanner()
    mapper = scanner.scan(tokenizer, verbose=verbose)
    if verbose:
        print(f"[VocabScanner] Done. Coverage: {scanner._coverage}/{scanner._vocab_size}")

    _save_to_disk(disk_path, scanner._token_map)

    _mapper_cache[key] = mapper
    return mapper
