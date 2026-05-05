#!/usr/bin/env python3
"""
governance/rag_memory.py
RAG-Memory fuer COGNITUM Engineering Agent
ChromaDB + Ollama nomic-embed-text Embeddings (urllib, kein subprocess)
"""
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_ADRS = "cognitum_adrs"
COLLECTION_DOCS = "cognitum_docs"


def _ollama_embed(text: str) -> Optional[List[float]]:
    """Ruft Ollama Embeddings via HTTP auf. Gibt None bei Fehler."""
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        EMBED_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding")
    except Exception:
        return None


class RAGMemory:
    def __init__(self, persist_dir: str = ".chroma_db"):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._adrs = self._client.get_or_create_collection(
                name=COLLECTION_ADRS,
                metadata={"hnsw:space": "cosine"},
            )
            self._docs = self._client.get_or_create_collection(
                name=COLLECTION_DOCS,
                metadata={"hnsw:space": "cosine"},
            )
            self._ready = True
        except ImportError:
            self._ready = False

    def embed(self, text: str) -> List[float]:
        """Embedding via Ollama nomic-embed-text. Fallback: leerer Vektor."""
        vec = _ollama_embed(text)
        if vec is None:
            return [0.0] * 768
        return vec

    def add_adr(self, adr_id: str, content: str, metadata: dict) -> bool:
        """Speichert ADR in Collection cognitum_adrs."""
        if not self._ready:
            return False
        try:
            vec = self.embed(content)
            self._adrs.upsert(
                ids=[adr_id],
                embeddings=[vec],
                documents=[content],
                metadatas=[metadata],
            )
            return True
        except Exception as e:
            print(f"  [RAG] add_adr Fehler: {e}")
            return False

    def add_document(self, doc_id: str, content: str, metadata: dict) -> bool:
        """Speichert beliebiges Dokument in Collection cognitum_docs."""
        if not self._ready:
            return False
        try:
            vec = self.embed(content)
            self._docs.upsert(
                ids=[doc_id],
                embeddings=[vec],
                documents=[content],
                metadatas=[metadata],
            )
            return True
        except Exception as e:
            print(f"  [RAG] add_document Fehler: {e}")
            return False

    def search(self, query: str, n_results: int = 3) -> List[dict]:
        """Hybrid-Suche ueber beide Collections. Gibt zusammengefuehrte Treffer zurueck."""
        if not self._ready:
            return []
        vec = self.embed(query)
        results = []

        for collection, ctype in [(self._adrs, "adr"), (self._docs, "doc")]:
            try:
                count = collection.count()
                if count == 0:
                    continue
                k = min(n_results, count)
                res = collection.query(
                    query_embeddings=[vec],
                    n_results=k,
                    include=["documents", "metadatas", "distances"],
                )
                for i, doc_id in enumerate(res["ids"][0]):
                    results.append({
                        "id": doc_id,
                        "type": ctype,
                        "content": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": res["distances"][0][i],
                    })
            except Exception:
                continue

        # Sortiert nach Relevanz (kleinste Distanz = relevantester)
        results.sort(key=lambda x: x["distance"])
        return results[:n_results]

    def get_context_for_spalten(self, problem: str) -> str:
        """Gibt formatierten Kontext-String fuer SPALTEN-Nodes zurueck (max 300 Zeichen)."""
        if not self._ready:
            return ""
        hits = self.search(problem, n_results=3)
        if not hits:
            return ""

        parts = []
        for h in hits:
            meta = h.get("metadata", {})
            label = meta.get("adr_id") or meta.get("title") or h["id"]
            snippet = h["content"][:80].replace("\n", " ").strip()
            parts.append(f"[{label}] {snippet}")

        context = " | ".join(parts)
        return context[:300]
