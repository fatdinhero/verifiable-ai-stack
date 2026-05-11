from __future__ import annotations

from typing import Optional

from llmjson._types import TokenType


class TokenMapper:
    def __init__(self, token_map: Optional[dict[int, TokenType]] = None):
        if token_map:
            self._id_to_type: dict[int, TokenType] = dict(token_map)
        else:
            self._id_to_type = {t.value: t for t in TokenType}

        self._type_to_ids: dict[TokenType, set[int]] = {}
        for tid, ttype in self._id_to_type.items():
            self._type_to_ids.setdefault(ttype, set()).add(tid)

    def id_to_type(self, token_id: int) -> Optional[TokenType]:
        return self._id_to_type.get(token_id)

    def type_to_ids(self, token_type: TokenType) -> set[int]:
        return self._type_to_ids.get(token_type, set())

    def valid_ids_for_types(
        self,
        valid_types: set[TokenType],
        vocab_size: int,
    ) -> set[int]:
        expanded = set(valid_types)
        if TokenType.STRING_KEY in expanded:
            expanded.add(TokenType.STRING)
        ids: set[int] = set()
        for ttype in expanded:
            for tid in self._type_to_ids.get(ttype, set()):
                if tid < vocab_size:
                    ids.add(tid)
        return ids
