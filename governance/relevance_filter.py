#!/usr/bin/env python3
"""
governance/relevance_filter.py
Hybrid-Relevanz-Filter: Block → Require → Embedding → LLM → Cache
"""
import hashlib
import json
import logging
import math
import re
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:7b"
CHROMA_PATH = str(Path(__file__).resolve().parents[1] / ".chroma_db")

_STANDARDS_RE = re.compile(
    r'\b(VDI|DIN|ISO|BSI|DSGVO|GDPR|EDPB|NIST|IEEE|ETSI|CEN|ENISA|CERT|CVE)\b',
    re.IGNORECASE,
)


def _normalize_umlauts(text: str) -> str:
    return (text
            .replace('ä', 'ae').replace('Ä', 'ae')
            .replace('ö', 'oe').replace('Ö', 'oe')
            .replace('ü', 'ue').replace('Ü', 'ue')
            .replace('ß', 'ss'))


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class RelevanceFilter:

    ENGINEERING_REFERENCES = [
        "EU AI Act Compliance-Anforderung Hochrisiko-KI",
        "VDI 2221 SPALTEN Engineering-Entscheidung",
        "DSGVO Datenschutz technische Massnahme",
        "BSI Sicherheitslücke Compliance-Gap",
        "DIN Norm Anforderung Engineering",
        "Sensor-Architektur Wearable Privacy-First",
        "Regulatorische Änderung technische Umsetzung",
        "Software-Architektur Entscheidung Make-Buy",
    ]

    BLOCK_KEYWORDS = [
        "militär", "military", "waffen", "weapons", "rüstung",
        "defense", "krieg", "war", "bundeswehr", "nato",
        "aktie", "börse", "sport", "fußball", "celebrity",
    ]

    REQUIRE_ONE_OF = [
        "ki", "ai", "software", "digital", "daten", "data",
        "compliance", "engineering", "sensor", "app", "tech",
        "norm", "recht", "regulation", "sicherheit", "datenschutz",
        "architektur", "api", "system", "cloud", "open source",
    ]

    def __init__(self):
        self._cache_collection = None
        self._ref_embeddings: Optional[list] = None
        self._block_patterns = self._build_block_patterns()
        self._init_cache()

    def _build_block_patterns(self) -> list:
        patterns = []
        for kw in self.BLOCK_KEYWORDS:
            norm_kw = re.escape(_normalize_umlauts(kw.lower()))
            # Prefix-Match: Wortgrenze vor Keyword, kein closing \b
            # → "militaer" trifft "militaerische", aber "war" nicht "software"
            patterns.append(re.compile(r'\b' + norm_kw, re.IGNORECASE))
        return patterns

    def _init_cache(self) -> None:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            self._cache_collection = client.get_or_create_collection(
                "cognitum_relevance_cache"
            )
        except Exception as e:
            logger.debug(f"ChromaDB Cache nicht verfügbar: {e}")

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]

    def _cache_get(self, text: str) -> Optional[dict]:
        if not self._cache_collection:
            return None
        try:
            key = self._cache_key(text)
            result = self._cache_collection.get(ids=[key])
            if result and result.get("documents"):
                return json.loads(result["documents"][0])
        except Exception:
            pass
        return None

    def _cache_set(self, text: str, result: dict) -> None:
        if not self._cache_collection:
            return
        try:
            key = self._cache_key(text)
            self._cache_collection.upsert(
                ids=[key],
                documents=[json.dumps(result, ensure_ascii=False)],
            )
        except Exception:
            pass

    def _get_embedding(self, text: str) -> Optional[list]:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("embedding")
        except Exception as e:
            logger.debug(f"Embedding-Fehler: {e}")
            return None

    def _get_ref_embeddings(self) -> Optional[list]:
        if self._ref_embeddings is not None:
            return self._ref_embeddings
        embeddings = []
        for ref in self.ENGINEERING_REFERENCES:
            emb = self._get_embedding(ref)
            if emb is None:
                return None
            embeddings.append(emb)
        self._ref_embeddings = embeddings
        return embeddings

    def _llm_score(self, text: str) -> dict:
        prompt = (
            "Bewerte Engineering-Relevanz 0.0-1.0 nach VDI 2221.\n"
            "Nur technische, regulatorische oder methodische Inhalte sind relevant.\n"
            f"Text: {text[:500]}\n\n"
            'Antworte NUR mit JSON: {"score": float, "category": str, "reason": str}'
        )
        payload = json.dumps({
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.2},
            "stream": False,
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["message"]["content"].strip()
                match = re.search(r'\{.*?\}', content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                    s = max(0.0, min(1.0, float(parsed.get("score", 0.5))))
                    return {
                        "score": round(s, 4),
                        "relevant": s >= 0.6,
                        "category": str(parsed.get("category", "unknown")),
                        "reason": str(parsed.get("reason", "")),
                        "method": "llm",
                    }
        except Exception as e:
            logger.debug(f"LLM-Score Fehler: {e}")
        return {
            "score": 0.4,
            "relevant": False,
            "category": "unknown",
            "reason": "llm_error",
            "method": "llm_fallback",
        }

    def _keyword_fallback_score(self, text: str, require_passed: bool) -> dict:
        if not require_passed:
            if _STANDARDS_RE.search(text):
                return {
                    "score": 0.65,
                    "relevant": True,
                    "category": "standards_heuristic",
                    "reason": "Bekanntes Norm-/Regulierungspräfix erkannt (Fallback)",
                    "method": "keyword_fallback",
                }
            return {
                "score": 0.1,
                "relevant": False,
                "category": "not_relevant",
                "reason": "Kein REQUIRE_ONE_OF Keyword und kein bekanntes Präfix",
                "method": "keyword_fallback",
            }
        lower = text.lower()
        matches = sum(
            1 for kw in self.REQUIRE_ONE_OF
            if re.search(r'\b' + re.escape(kw) + r'\b', lower)
        )
        s = round(min(0.55 + matches * 0.06, 0.85), 4)
        return {
            "score": s,
            "relevant": s >= 0.6,
            "category": "keyword_match",
            "reason": f"{matches} REQUIRE_ONE_OF Keywords gefunden",
            "method": "keyword_fallback",
        }

    def score(self, text: str) -> dict:
        """
        Hybrid-Relevanz-Score.
        Returns dict: score (float 0-1), relevant (bool), method (str), reason (str).
        """
        lower = text.lower()
        norm_lower = _normalize_umlauts(lower)

        # 1. Block-Filter (Prefix-Match nach Umlaut-Normalisierung)
        for pattern in self._block_patterns:
            if pattern.search(norm_lower):
                return {
                    "score": 0.0,
                    "relevant": False,
                    "category": "blocked",
                    "reason": f"Block-Keyword: {pattern.pattern}",
                    "method": "block_filter",
                }

        # 2. Require-Filter (soft — kein hard-return, setzt nur Flag)
        require_passed = any(
            re.search(r'\b' + re.escape(kw) + r'\b', lower)
            for kw in self.REQUIRE_ONE_OF
        )

        # Cache-Lookup
        cached = self._cache_get(text)
        if cached:
            return cached

        # 3. Embedding via Ollama nomic-embed-text
        text_emb = self._get_embedding(text)
        if text_emb is None:
            # Graceful Fallback: nur Keyword-Filter
            result = self._keyword_fallback_score(text, require_passed)
            self._cache_set(text, result)
            return result

        ref_embeddings = self._get_ref_embeddings()
        if ref_embeddings is None:
            result = self._keyword_fallback_score(text, require_passed)
            self._cache_set(text, result)
            return result

        similarities = [_cosine_similarity(text_emb, ref) for ref in ref_embeddings]
        max_similarity = max(similarities) if similarities else 0.0

        # 4. Hohe Similarity → direkt relevant, kein LLM-Call
        if max_similarity > 0.75:
            result = {
                "score": round(max_similarity, 4),
                "relevant": True,
                "category": "engineering",
                "reason": f"Embedding-Similarity: {max_similarity:.3f}",
                "method": "embedding",
                "embedding_score": round(max_similarity, 4),
            }
            self._cache_set(text, result)
            return result

        # 5. Niedrige Similarity → nicht relevant, kein LLM-Call
        if max_similarity < 0.25:
            result = {
                "score": 0.1 if not require_passed else round(max_similarity, 4),
                "relevant": False,
                "category": "not_relevant",
                "reason": f"Embedding-Similarity zu niedrig: {max_similarity:.3f}",
                "method": "embedding",
                "embedding_score": round(max_similarity, 4),
            }
            self._cache_set(text, result)
            return result

        # 6. Grenzfall (0.25–0.75) → LLM-Call via qwen2.5:7b
        llm_result = self._llm_score(text)
        llm_result["embedding_score"] = round(max_similarity, 4)
        self._cache_set(text, llm_result)
        return llm_result

    def is_relevant(self, text: str, threshold: float = 0.6) -> bool:
        """Gibt score().relevant zurück (score >= threshold)."""
        result = self.score(text)
        return result["score"] >= threshold
