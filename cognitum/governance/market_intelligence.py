#!/usr/bin/env python3
"""
governance/market_intelligence.py
MarketScanner — Web-Suche (DuckDuckGo Lite) + LLM-Extraktion + ChromaDB.
Kein API-Key, nur urllib + html.parser + qwen2.5:7b.
"""
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional

COLLECTION_NAME = "cognitum_market_channels"
OLLAMA_URL  = "http://localhost:11434/api/chat"
EMBED_URL   = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
MODEL       = "qwen2.5:7b"
DDG_URL     = "https://lite.duckduckgo.com/lite/"

REPO_ROOT   = Path(__file__).resolve().parents[1]
CHROMA_PATH = str(REPO_ROOT / ".chroma_db")

KNOWN_CHANNELS: List[Dict] = [
    {
        "name": "Gumroad",
        "url": "https://gumroad.com",
        "category": "digital-products",
        "target_audience": "Solo-Dev",
        "price_range": "49-499 EUR",
        "effort_level": "minimal",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "schnell",
        "confidence_score": 0.90,
        "source": "seed",
    },
    {
        "name": "JetBrains Marketplace",
        "url": "https://plugins.jetbrains.com",
        "category": "plugins",
        "target_audience": "Developers",
        "price_range": "subscription",
        "effort_level": "mittel",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "mittelfristig",
        "confidence_score": 0.85,
        "source": "seed",
    },
    {
        "name": "Hugging Face Datasets Hub",
        "url": "https://huggingface.co/datasets",
        "category": "ml-datasets",
        "target_audience": "ML-Teams",
        "price_range": "kostenlos / community",
        "effort_level": "minimal",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "langsam",
        "confidence_score": 0.80,
        "source": "seed",
    },
    {
        "name": "datarade.ai",
        "url": "https://datarade.ai",
        "category": "b2b-datasets",
        "target_audience": "Enterprise",
        "price_range": "500-50000 EUR",
        "effort_level": "hoch",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "langsam",
        "confidence_score": 0.88,
        "source": "seed",
    },
    {
        "name": "RapidAPI",
        "url": "https://rapidapi.com",
        "category": "apis",
        "target_audience": "Developers",
        "price_range": "usage-based",
        "effort_level": "mittel",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "mittelfristig",
        "confidence_score": 0.82,
        "source": "seed",
    },
    {
        "name": "MCPize",
        "url": "https://mcpize.com",
        "category": "mcp-servers",
        "target_audience": "AI-Developers",
        "price_range": "subscription",
        "effort_level": "minimal",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "schnell",
        "confidence_score": 0.75,
        "source": "seed",
    },
    {
        "name": "Fiverr",
        "url": "https://fiverr.com",
        "category": "services-gigs",
        "target_audience": "Solo-Dev",
        "price_range": "project-based",
        "effort_level": "minimal",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "sofort",
        "confidence_score": 0.88,
        "source": "seed",
    },
    {
        "name": "AWS Data Exchange",
        "url": "https://aws.amazon.com/data-exchange",
        "category": "enterprise-datasets",
        "target_audience": "Enterprise",
        "price_range": "1000+ EUR",
        "effort_level": "hoch",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "langsam",
        "confidence_score": 0.85,
        "source": "seed",
    },
    {
        "name": "Anthropic MCP Registry",
        "url": "https://modelcontextprotocol.io",
        "category": "mcp-servers",
        "target_audience": "AI-Developers",
        "price_range": "kostenlos",
        "effort_level": "minimal",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "mittelfristig",
        "confidence_score": 0.78,
        "source": "seed",
    },
    {
        "name": "Direct B2B / Cold Outreach",
        "url": "https://linkedin.com",
        "category": "b2b-direct",
        "target_audience": "DACH-Mittelstand",
        "price_range": "enterprise",
        "effort_level": "hoch",
        "halal_compatible": True,
        "dsgvo_compatible": True,
        "revenue_speed": "langsam",
        "confidence_score": 0.80,
        "source": "seed",
    },
]


# ─── DuckDuckGo Lite Parser ───────────────────────────────────────────────────

class _DDGParser(HTMLParser):
    """Extrahiert Ergebnisse (title, url, snippet) aus DuckDuckGo Lite HTML."""

    def __init__(self):
        super().__init__()
        self._links: List[Dict[str, str]] = []
        self._snippets: List[str] = []
        self._in_link = False
        self._in_snippet = False
        self._cur_url = ""
        self._cur_title = ""
        self._cur_snippet = ""

    def handle_starttag(self, tag: str, attrs):
        d = dict(attrs)
        cls = d.get("class", "")
        if tag == "a" and "result-link" in cls:
            self._in_link = True
            href = d.get("href", "")
            url = href
            if "uddg=" in href:
                try:
                    raw = href.split("uddg=")[1].split("&")[0]
                    url = urllib.parse.unquote(raw)
                except Exception:
                    pass
            self._cur_url = url if url.startswith("http") else ""
            self._cur_title = ""
        elif tag == "td" and "result-snippet" in cls:
            self._in_snippet = True
            self._cur_snippet = ""
        elif tag == "span" and "result-snippet" in cls:
            self._in_snippet = True
            self._cur_snippet = ""

    def handle_endtag(self, tag: str):
        if tag == "a" and self._in_link:
            self._in_link = False
            title = self._cur_title.strip()
            if title and self._cur_url:
                self._links.append({"title": title, "url": self._cur_url})
        elif tag in ("td", "span") and self._in_snippet:
            self._in_snippet = False
            snippet = self._cur_snippet.strip()
            if snippet:
                self._snippets.append(snippet)

    def handle_data(self, data: str):
        text = data.strip()
        if not text:
            return
        if self._in_link:
            self._cur_title += text
        elif self._in_snippet:
            self._cur_snippet += " " + text

    def get_results(self, top_n: int = 5) -> List[Dict[str, str]]:
        out = []
        for i, link in enumerate(self._links[:top_n]):
            snippet = self._snippets[i] if i < len(self._snippets) else ""
            out.append({"title": link["title"], "url": link["url"], "snippet": snippet})
        return out


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _channel_id(name: str) -> str:
    return "mc_" + hashlib.md5(name.lower().strip().encode()).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _embed(text: str) -> Optional[List[float]]:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        EMBED_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("embedding")
    except Exception:
        return None


def _call_llm(prompt: str, system: str, temperature: float = 0.3) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user",   "content": prompt}],
        "options": {"temperature": temperature},
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())["message"]["content"].strip()
    except Exception as e:
        return f"[LLM-ERROR] {e}"


def _channel_doc(ch: Dict) -> str:
    return (
        f"{ch.get('name', '')} | {ch.get('category', '')} | "
        f"{ch.get('target_audience', '')} | {ch.get('price_range', '')} | "
        f"{ch.get('revenue_speed', '')}"
    )


# ─── MarketScanner ────────────────────────────────────────────────────────────

class MarketScanner:
    """Scannt Web + ChromaDB fuer Revenue-Kanaele. Kein API-Key erforderlich."""

    def __init__(self, chroma_path: str = CHROMA_PATH):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=chroma_path)
            self._col = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self._ready = True
        except ImportError:
            self._ready = False
            self._col = None

    # ── Public API ────────────────────────────────────────────────────────────

    def scan(self, domain: str, query: str) -> List[Dict]:
        """DuckDuckGo Lite → LLM-Extraktion → ChromaDB upsert. Gibt neue/aktualisierte Kanaele zurueck."""
        raw_results = self._ddg_search(query, top_n=5)
        if not raw_results:
            return []

        extracted = self._llm_extract_channels(raw_results, domain)
        saved = []
        for ch in extracted:
            ch["last_verified"] = _now_iso()
            ch.setdefault("source", f"ddg:{query[:40]}")
            ch.setdefault("domain", domain)
            if self._upsert_channel(ch):
                saved.append(ch)
        return saved

    def get_channels_for_domain(self, domain: str, max_age_days: int = 30) -> List[Dict]:
        """Gibt alle Kanaele aus ChromaDB sortiert nach confidence_score DESC."""
        if not self._ready:
            return [dict(ch) for ch in KNOWN_CHANNELS]

        try:
            # Semantische Suche mit Domain als Query
            emb = _embed(f"revenue channel marketplace {domain}")
            if emb:
                res = self._col.query(
                    query_embeddings=[emb],
                    n_results=min(50, max(1, self._col.count())),
                    include=["documents", "metadatas", "distances"],
                )
                metas = res.get("metadatas", [[]])[0]
            else:
                # Fallback: alle Eintraege holen
                all_res = self._col.get(include=["metadatas"])
                metas = all_res.get("metadatas", [])

            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            channels = []
            for m in metas:
                if not m:
                    continue
                lv = m.get("last_verified", "")
                if lv:
                    try:
                        dt = datetime.fromisoformat(lv.replace("Z", "+00:00"))
                        if dt < cutoff:
                            continue
                    except ValueError:
                        pass
                channels.append(dict(m))

            channels.sort(key=lambda c: float(c.get("confidence_score", 0)), reverse=True)
            return channels

        except Exception:
            return [dict(ch) for ch in KNOWN_CHANNELS]

    def seed_known_channels(self) -> int:
        """Fuellt ChromaDB mit bekannten Kanaelen (idempotent). Gibt Anzahl gespeicherter zurueck."""
        if not self._ready:
            return 0

        now = _now_iso()
        seeded = 0
        for ch in KNOWN_CHANNELS:
            ch_copy = dict(ch)
            ch_copy["last_verified"] = now
            ch_copy["domain"] = "general"
            if self._upsert_channel(ch_copy, force_if_seed=True):
                seeded += 1
        print(f"  🌱 seed_known_channels: {seeded}/{len(KNOWN_CHANNELS)} gespeichert")
        return seeded

    def get_all_channels_fast(self) -> List[Dict]:
        """Schneller Direktzugriff auf alle Kanaele ohne Embedding-Aufruf."""
        if not self._ready:
            return [dict(ch) for ch in KNOWN_CHANNELS]
        try:
            all_res = self._col.get(include=["metadatas"])
            metas = all_res.get("metadatas", [])
            return [dict(m) for m in metas if m]
        except Exception:
            return [dict(ch) for ch in KNOWN_CHANNELS]

    def build_morphologie_matrix(self, domain: str, scan_query: str) -> Dict[str, List[str]]:
        """Kombiniert ChromaDB-Kanaele + Web-Scan zu Morphologie-Matrix fuer node_A."""
        channels = self.get_channels_for_domain(domain)

        # Zusaetzliche Kanaele via Scan (Top-5 aus DuckDuckGo)
        try:
            new_channels = self.scan(domain, scan_query)
            for ch in new_channels:
                if ch.get("name") and not any(
                    c.get("name", "").lower() == ch["name"].lower() for c in channels
                ):
                    channels.append(ch)
        except Exception:
            pass

        kanal_namen = [c["name"] for c in channels if c.get("name")]
        # Deduplizieren, Reihenfolge beibehalten
        seen: set = set()
        unique_kanaele = []
        for n in kanal_namen:
            key = n.lower()
            if key not in seen:
                seen.add(key)
                unique_kanaele.append(n)

        top10 = unique_kanaele[:10] or ["Gumroad", "Fiverr", "datarade.ai", "RapidAPI"]
        # Kanal LAST damit itertools.product in morphologischer_kasten alle
        # Kanaele in den ersten Varianten abdeckt (aendert sich am schnellsten).
        return {
            "Zeithorizont": ["sofort (<4W)", "kurzfristig (1-3M)"],
            "Produkt-Typ":  ["Dienstleistung/Gig", "Plugin/CLI", "Datensatz"],
            "Kanal":        top10,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _ddg_search(self, query: str, top_n: int = 5) -> List[Dict[str, str]]:
        """GET DuckDuckGo Lite, parse HTML, gib Top-N Ergebnisse zurueck."""
        params = urllib.parse.urlencode({"q": query, "kl": "de-de"})
        url = f"{DDG_URL}?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            parser = _DDGParser()
            parser.feed(html)
            results = parser.get_results(top_n)
            return results
        except urllib.error.HTTPError as e:
            print(f"    ⚠️  DDG HTTP {e.code}: {e.reason}")
            return []
        except Exception as e:
            print(f"    ⚠️  DDG-Suche fehlgeschlagen: {e}")
            return []

    def _llm_extract_channels(
        self, search_results: List[Dict[str, str]], domain: str
    ) -> List[Dict]:
        """LLM extrahiert strukturierte Kanal-Infos aus Suchergebnissen."""
        snippets = "\n".join(
            f"[{i+1}] {r['title']} | {r['url']}\n    {r['snippet']}"
            for i, r in enumerate(search_results)
        )
        system = (
            "Du bist ein Market-Intelligence-Analyst. Antworte NUR mit validem JSON. "
            "Kein Markdown, keine Erklaerungen."
        )
        prompt = (
            f"Domain: {domain}\n"
            f"Suchergebnisse:\n{snippets}\n\n"
            "Extrahiere bis zu 3 relevante Verkaufs-Plattformen oder Marktplaetze. "
            "Antworte mit JSON-Array:\n"
            '[\n'
            '  {\n'
            '    "name": "Plattformname",\n'
            '    "url": "https://...",\n'
            '    "category": "z.B. marketplace/api/dataset",\n'
            '    "target_audience": "z.B. developers/enterprise",\n'
            '    "price_range": "z.B. free/subscription/500-5000 EUR",\n'
            '    "effort_level": "minimal|mittel|hoch",\n'
            '    "halal_compatible": true,\n'
            '    "dsgvo_compatible": true,\n'
            '    "revenue_speed": "sofort|schnell|mittelfristig|langsam",\n'
            '    "confidence_score": 0.7\n'
            '  }\n'
            ']'
        )
        raw = _call_llm(prompt, system, temperature=0.2)

        # JSON aus Antwort extrahieren
        try:
            # Versuche direkt parsen
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Suche erstes JSON-Array im Text
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        return []

    def _upsert_channel(self, ch: Dict, force_if_seed: bool = False) -> bool:
        """Speichert oder aktualisiert einen Kanal in ChromaDB. True wenn gespeichert."""
        if not self._ready:
            return False
        name = ch.get("name", "").strip()
        if not name:
            return False

        doc = _channel_doc(ch)
        emb = _embed(doc)

        meta: Dict = {
            "name":             str(name),
            "url":              str(ch.get("url", "")),
            "category":         str(ch.get("category", "")),
            "target_audience":  str(ch.get("target_audience", "")),
            "price_range":      str(ch.get("price_range", "")),
            "effort_level":     str(ch.get("effort_level", "mittel")),
            "halal_compatible": bool(ch.get("halal_compatible", True)),
            "dsgvo_compatible": bool(ch.get("dsgvo_compatible", True)),
            "revenue_speed":    str(ch.get("revenue_speed", "mittelfristig")),
            "last_verified":    str(ch.get("last_verified", _now_iso())),
            "confidence_score": float(ch.get("confidence_score", 0.6)),
            "source":           str(ch.get("source", "scan")),
            "domain":           str(ch.get("domain", "general")),
        }

        chan_id = _channel_id(name)
        try:
            if emb:
                self._col.upsert(
                    ids=[chan_id],
                    embeddings=[emb],
                    documents=[doc],
                    metadatas=[meta],
                )
            else:
                self._col.upsert(
                    ids=[chan_id],
                    documents=[doc],
                    metadatas=[meta],
                )
            return True
        except Exception as e:
            print(f"    ⚠️  ChromaDB upsert fehlgeschlagen ({name}): {e}")
            return False
