"""
gateway/sanitizer.py — Proprietary-term alias sanitizer.

Replaces proprietary COGNITUM terms with neutral aliases before any
text leaves the local environment (corpus export, API payloads, etc.).
No external dependencies — only stdlib re and json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict

_DICT_PATH = Path(__file__).parent / "alias_dictionary.json"


class AliasDictionary:
    """Loads alias_dictionary.json and provides sanitize / deanonymize."""

    def __init__(self, dict_path: Path = _DICT_PATH) -> None:
        with open(dict_path, encoding="utf-8") as fh:
            self._aliases: Dict[str, str] = json.load(fh)
        # Build reverse map for deanonymization.
        self._reverse: Dict[str, str] = {v: k for k, v in self._aliases.items()}
        # Pre-compile a single regex for forward pass (longest terms first to
        # avoid partial matches, e.g. "VeriEthicCore" before "Core").
        terms = sorted(self._aliases.keys(), key=len, reverse=True)
        pattern = "|".join(re.escape(t) for t in terms)
        self._fwd_re = re.compile(pattern, re.IGNORECASE)
        # Reverse regex
        rev_terms = sorted(self._reverse.keys(), key=len, reverse=True)
        rev_pattern = "|".join(re.escape(t) for t in rev_terms)
        self._rev_re = re.compile(rev_pattern, re.IGNORECASE)

    def sanitize(self, text: str) -> str:
        """Replace all proprietary terms with their public aliases."""
        def _replace(m: re.Match) -> str:
            original = m.group(0)
            # Preserve leading capital if the original term is capitalized.
            alias = self._aliases.get(original) or self._aliases.get(original.lower(), original)
            # Try exact case first, then title-cased key.
            for key in (original, original.title(), original.upper(), original.lower()):
                if key in self._aliases:
                    alias = self._aliases[key]
                    break
            return alias

        return self._fwd_re.sub(_replace, text)

    def deanonymize(self, text: str) -> str:
        """Restore original proprietary terms from their aliases."""
        def _restore(m: re.Match) -> str:
            alias = m.group(0)
            return self._reverse.get(alias, alias)

        return self._rev_re.sub(_restore, text)


# Module-level singleton — import and use directly.
_dictionary = AliasDictionary()


def sanitize(text: str) -> str:
    """Sanitize *text* using the module-level AliasDictionary."""
    return _dictionary.sanitize(text)


def deanonymize(text: str) -> str:
    """Restore original terms in *text* using the module-level AliasDictionary."""
    return _dictionary.deanonymize(text)
