#!/Users/datalabel.tech/COS/cognitum/.venv/bin/python3
"""
scripts/chat_indexer.py
KI-Chat-Exporte (Claude, ChatGPT, Grok, Generic) → ChromaDB cognitum_chat_history
Embeddings: nomic-embed-text via Ollama | Chunking: 500 Tok / 50 Overlap (tiktoken)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import uuid

import numpy as np
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
import ollama
import requests
import tiktoken
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# ─── CONFIG ──────────────────────────────────────────────────────────────────
CHROMA_PATH    = str(Path(__file__).parent.parent / ".chroma_db")
COLLECTION     = "cognitum_chat_history"
EMBED_MODEL    = "nomic-embed-text"
CHUNK_TOKENS   = 500
CHUNK_OVERLAP  = 50
WEBHOOK_PORT   = 8222
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ─── TOKENIZER ───────────────────────────────────────────────────────────────
_enc = tiktoken.get_encoding("cl100k_base")

def _token_len(text: str) -> int:
    return len(_enc.encode(text))

def chunk_text(text: str) -> List[str]:
    tokens = _enc.encode(text)
    chunks, start = [], 0
    while start < len(tokens):
        end = min(start + CHUNK_TOKENS, len(tokens))
        chunks.append(_enc.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start += CHUNK_TOKENS - CHUNK_OVERLAP
    return chunks or [text]

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def sha_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def _is_base64_blob(text: str) -> bool:
    """True wenn >50% des Texts aus langen zusammenhängenden Base64-Blöcken besteht.
    Echter Base64 hat keine Leerzeichen und Läufe von ≥60 Zeichen."""
    import re
    stripped = text.strip()
    if len(stripped) < 80:
        return False
    # Lange Base64-Blöcke ohne Leerzeichen (mind. 60 Zeichen am Stück)
    b64_runs = re.findall(r'[A-Za-z0-9+/]{60,}={0,2}', stripped)
    if not b64_runs:
        return False
    b64_total = sum(len(r) for r in b64_runs)
    return b64_total / len(stripped) > 0.50

def embed(text: str) -> List[float]:
    try:
        return ollama.embeddings(model=EMBED_MODEL, prompt=text[:4096]).embedding
    except Exception:
        return [0.0] * 768

def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

# ─── PARSERS ─────────────────────────────────────────────────────────────────
Message = Dict[str, Any]

def _msg(platform: str, role: str, content: str,
         timestamp: str, source: str) -> Message:
    return {
        "id": sha_id(content),
        "platform": platform,
        "role": role,
        "content": content,
        "timestamp": timestamp,
        "source_file": source,
    }

def _extract_text(content: Any) -> str:
    """Normalisiert content aus allen Claude-Formaten zu einem String."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        # conversations.json: [{type: "text", text: "..."}]
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "text" in item:
                    parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts).strip()
    if isinstance(content, dict):
        # design_chats: {content: "...", contentBlocks: [...]}
        text = content.get("content", "")
        if isinstance(text, str) and text.strip():
            return text.strip()
        # Fallback: contentBlocks
        for block in content.get("contentBlocks", []):
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "").strip()
    return ""

def _parse_chat_messages(entries: List[dict], source: str) -> List[Message]:
    """Parst chat_messages[] — Format aus conversations.json und projects/*.json."""
    msgs = []
    for m in entries:
        raw_role = m.get("sender", m.get("role", "human"))
        role = "user" if raw_role == "human" else "assistant"
        text = _extract_text(m.get("content", m.get("text", "")))
        if not text:
            text = _extract_text(m.get("text", ""))
        if not text:
            continue
        ts = m.get("created_at", datetime.now(timezone.utc).isoformat())
        msgs.append(_msg("claude", role, text, ts, source))
    return msgs

def _parse_design_messages(entries: List[dict], source: str) -> List[Message]:
    """Parst messages[] — Format aus design_chats/*.json."""
    msgs = []
    for m in entries:
        role = m.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        text = _extract_text(m.get("content", ""))
        if not text:
            continue
        ts = m.get("created_at", m.get("timestamp", datetime.now(timezone.utc).isoformat()))
        if isinstance(ts, dict):
            ts = ts.get("$date", datetime.now(timezone.utc).isoformat())
        msgs.append(_msg("claude", role, text, str(ts), source))
    return msgs

def parse_claude(path: str) -> List[Message]:
    """Claude.ai ZIP Export: conversations.json (446 Chats) + design_chats/*.json."""
    msgs = []

    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            for fname in z.namelist():
                if not fname.endswith(".json"):
                    continue
                try:
                    raw = json.loads(z.read(fname).decode("utf-8"))
                except Exception:
                    continue
                source = Path(fname).name

                if fname == "conversations.json" and isinstance(raw, list):
                    # Haupt-Export: Liste aller Conversations
                    for conv in raw:
                        if isinstance(conv, dict):
                            msgs.extend(_parse_chat_messages(conv.get("chat_messages", []), source))

                elif fname.startswith("design_chats/") and isinstance(raw, dict):
                    msgs.extend(_parse_design_messages(raw.get("messages", []), source))

                elif fname.startswith("projects/") and isinstance(raw, dict):
                    msgs.extend(_parse_chat_messages(raw.get("chat_messages", []), source))

    else:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        source = Path(path).name
        convs = raw if isinstance(raw, list) else [raw]
        for conv in convs:
            if isinstance(conv, dict):
                msgs.extend(_parse_chat_messages(conv.get("chat_messages", []), source))

    return msgs

def parse_chatgpt(path: str) -> List[Message]:
    """ChatGPT ZIP Export: conversations.json im ZIP oder direkte JSON."""
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            candidates = [n for n in z.namelist() if "conversations" in n and n.endswith(".json")]
            fname = candidates[0] if candidates else next((n for n in z.namelist() if n.endswith(".json")), None)
            if not fname:
                return []
            raw = json.loads(z.read(fname).decode("utf-8"))
    else:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))

    msgs = []
    for conv in (raw if isinstance(raw, list) else [raw]):
        for node in conv.get("mapping", {}).values():
            m = node.get("message")
            if not m:
                continue
            role = m.get("author", {}).get("role", "unknown")
            if role not in ("user", "assistant"):
                continue
            parts = m.get("content", {}).get("parts", [])
            text  = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
            if not text:
                continue
            ct = m.get("create_time")
            ts = datetime.fromtimestamp(ct, tz=timezone.utc).isoformat() if ct else datetime.now(timezone.utc).isoformat()
            msgs.append(_msg("chatgpt", role, text, ts, Path(path).name))
    return msgs

def parse_grok(path: str) -> List[Message]:
    """Grok Browser-Scrape JSON: flexibles Format."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else raw.get("messages", raw.get("conversations", [raw]))
    msgs = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        text = e.get("text", e.get("content", e.get("message", "")))
        if not text:
            continue
        raw_role = str(e.get("role", e.get("author", "user"))).lower()
        role = "assistant" if ("grok" in raw_role or raw_role == "assistant") else "user"
        ts   = str(e.get("timestamp", e.get("created_at", datetime.now(timezone.utc).isoformat())))
        msgs.append(_msg("grok", role, str(text), ts, Path(path).name))
    return msgs

def _parse_deepseek_conv(conv: dict, source: str) -> List[Message]:
    """Traversiert einen DeepSeek Conversation-Baum (mapping) und extrahiert Messages."""
    msgs: List[Message] = []
    mapping = conv.get("mapping", {})

    def _traverse(node_id: str, visited: set) -> None:
        if node_id in visited or node_id not in mapping:
            return
        visited.add(node_id)
        node = mapping[node_id]
        message = node.get("message")
        if message:
            ts        = str(message.get("inserted_at", ""))
            fragments = message.get("fragments", [])
            for frag in fragments:
                ftype   = frag.get("type", "")
                content = str(frag.get("content", "")).strip()
                if not content:
                    continue
                if ftype == "REQUEST":
                    role = "user"
                elif ftype in ("THINK", "RESPONSE"):
                    role = "assistant"
                else:
                    role = "user"
                msgs.append(_msg("deepseek", role, content, ts, source))
        for child_id in node.get("children", []):
            _traverse(child_id, visited)

    _traverse("root", set())
    return msgs


def parse_deepseek(path: str) -> List[Message]:
    """DeepSeek Export: ZIP mit conversations.json (mapping-Baum, fragments: REQUEST/THINK/RESPONSE)."""
    msgs: List[Message] = []
    src = Path(path).name

    def _process(raw: Any) -> None:
        convs = raw if isinstance(raw, list) else [raw]
        for conv in convs:
            if isinstance(conv, dict) and "mapping" in conv:
                msgs.extend(_parse_deepseek_conv(conv, src))

    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            if "conversations.json" in z.namelist():
                raw = json.loads(z.read("conversations.json").decode("utf-8", errors="replace"))
                _process(raw)
    else:
        raw = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
        _process(raw)

    return msgs


def parse_generic(path: str) -> List[Message]:
    """Fallback: .py/.txt/.md als Dokument, JSON nach gängigen Strukturen."""
    p   = Path(path)
    src = p.name
    now = datetime.now(timezone.utc).isoformat()

    if p.suffix in (".py", ".txt", ".md", ".yaml", ".json"):
        text = p.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return []
        role = "assistant" if p.suffix == ".py" else "user"
        # Versuche JSON zu parsen für mehr Struktur
        if p.suffix == ".json":
            try:
                raw = json.loads(text)
                entries = raw if isinstance(raw, list) else [raw]
                msgs = []
                for e in entries:
                    if isinstance(e, dict):
                        body = e.get("content", e.get("text", e.get("message", str(e))))
                        r    = e.get("role", "user")
                        t    = str(e.get("timestamp", e.get("created_at", now)))
                        msgs.append(_msg("generic", r, str(body), t, src))
                    elif isinstance(e, str):
                        msgs.append(_msg("generic", "user", e, now, src))
                if msgs:
                    return msgs
            except Exception:
                pass
        return [_msg("generic", role, text, now, src)]
    return []

def detect_platform(path: str) -> str:
    p = Path(path)
    if p.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if "conversations.json" in names:
                # Unterscheide DeepSeek (fragments) von ChatGPT (parts)
                try:
                    raw   = json.loads(z.read("conversations.json").decode("utf-8", errors="replace"))
                    convs = raw if isinstance(raw, list) else [raw]
                    if convs and isinstance(convs[0], dict):
                        mapping = convs[0].get("mapping", {})
                        for node in mapping.values():
                            msg = node.get("message")
                            if msg and "fragments" in msg:
                                return "deepseek"
                except Exception:
                    pass
                return "chatgpt"
        if any(n.startswith(("projects/", "design_chats/")) for n in names):
            return "claude"
        return "claude"  # Claude-Default für unbekannte ZIPs
    if p.suffix in (".py", ".txt", ".md", ".yaml"):
        return "generic"
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        first = raw[0] if isinstance(raw, list) and raw else raw
        if isinstance(first, dict):
            if "chat_messages" in first or first.get("sender") in ("human", "assistant"):
                return "claude"
            if "mapping" in first:
                return "chatgpt"
    except Exception:
        pass
    return "generic"

PARSERS = {
    "claude":    parse_claude,
    "chatgpt":   parse_chatgpt,
    "grok":      parse_grok,
    "deepseek":  parse_deepseek,
    "generic":   parse_generic,
}

# ─── INDEXER ─────────────────────────────────────────────────────────────────
def index_file(path: str, platform: str = "auto") -> Tuple[int, int]:
    """Indexiert eine Datei. Gibt (neue_chunks, übersprungene_duplikate) zurück."""
    if platform == "auto":
        platform = detect_platform(path)
    parser   = PARSERS.get(platform, parse_generic)
    messages = parser(path)
    if not messages:
        return 0, 0

    col = get_collection()
    new = dup = 0

    for msg in messages:
        for i, chunk in enumerate(chunk_text(msg["content"])):
            if _token_len(chunk) < 8:           # Sehr kurze Chunks → kollabierte Embeddings
                continue
            if _is_base64_blob(chunk):           # Base64-kodierter Code → kein Semantik-Wert
                continue
            chunk_id = sha_id(chunk)
            if col.get(ids=[chunk_id])["ids"]:
                dup += 1
                continue
            col.upsert(
                ids=[chunk_id],
                embeddings=[embed(chunk)],
                documents=[chunk],
                metadatas=[{
                    "platform":    msg["platform"],
                    "role":        msg["role"],
                    "timestamp":   msg["timestamp"],
                    "source_file": msg["source_file"],
                    "chunk_index": i,
                    "msg_id":      msg["id"],
                }],
            )
            new += 1

    return new, dup

def index_directory(dir_path: str, platform: str = "auto") -> Tuple[int, int]:
    """Indexiert alle Dateien in einem Verzeichnis rekursiv."""
    exts  = {".json", ".txt", ".md", ".py", ".yaml", ".zip"}
    files = [f for f in Path(dir_path).rglob("*") if f.is_file() and f.suffix in exts]
    total_new = total_dup = 0
    for f in files:
        print(f"  → {f.name}", end=" ", flush=True)
        try:
            n, d = index_file(str(f), platform)
            print(f"({n} neu, {d} dup)")
            total_new += n
            total_dup += d
        except Exception as e:
            print(f"FEHLER: {e}")
    return total_new, total_dup

# ─── STATUS + TELEGRAM ───────────────────────────────────────────────────────
def collection_size() -> int:
    try:
        return get_collection().count()
    except Exception:
        return -1

def send_telegram(text: str) -> None:
    token   = os.environ.get("TELEGRAM_TOKEN", TELEGRAM_TOKEN)
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass

def status_report(new: int, dup: int, label: str = "") -> str:
    total = collection_size()
    report = (
        f"✅ Chat-Index Update{(' — ' + label) if label else ''}\n"
        f"  Neue Chunks:        {new}\n"
        f"  Duplikate skip:     {dup}\n"
        f"  Collection gesamt:  {total}\n"
        f"  Zeitstempel:        {datetime.now(timezone.utc).isoformat()[:19]}Z"
    )
    print(report)
    send_telegram(report)
    return report

# ─── SEARCH ──────────────────────────────────────────────────────────────────
def search_chats(query: str, n: int = 3) -> List[dict]:
    """Cosine-Suche via numpy — Workaround für ChromaDB 1.5.x RustBindingsAPI Distance-Bug."""
    col = get_collection()
    count = col.count()
    if count == 0:
        return []

    q_vec = np.array(embed(query), dtype=np.float32)
    q_norm = np.linalg.norm(q_vec)
    if q_norm == 0:
        return []

    # Lade alle Embeddings in Batches (ChromaDB 1.5.x get() ist stabil)
    BATCH = 2000
    all_ids, all_docs, all_metas, all_vecs = [], [], [], []
    offset = 0
    while offset < count:
        batch = col.get(
            limit=BATCH,
            offset=offset,
            include=["embeddings", "documents", "metadatas"],
        )
        all_ids   += batch["ids"]
        all_docs  += batch["documents"]
        all_metas += batch["metadatas"]
        all_vecs  += list(batch["embeddings"])
        offset += len(batch["ids"])
        if len(batch["ids"]) < BATCH:
            break

    mat = np.array(all_vecs, dtype=np.float32)          # (N, 768)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)   # (N, 1)
    norms[norms == 0] = 1e-9
    mat_norm = mat / norms

    scores = mat_norm @ (q_vec / q_norm)                 # cosine similarity

    # Kollabierte Embeddings filtern: kurze Chunks (<80 Zeichen) haben oft identische Vektoren
    valid = np.ones(len(scores), dtype=bool)
    for idx in range(len(scores)):
        if len(all_docs[idx]) < 80:
            valid[idx] = False
    valid_indices = np.where(valid)[0]
    top_idx = valid_indices[np.argsort(scores[valid_indices])[::-1][:n]]

    return [
        {
            "rank":     rank + 1,
            "id":       all_ids[i],
            "content":  all_docs[i],
            "metadata": all_metas[i],
            "distance": float(1.0 - scores[i]),
        }
        for rank, i in enumerate(top_idx)
    ]

# ─── FASTAPI WEBHOOK ─────────────────────────────────────────────────────────
app    = FastAPI(title="COGNITUM Chat Indexer", version="1.0.0")
_jobs: Dict[str, Dict] = {}

class IndexRequest(BaseModel):
    path:     str
    platform: str = "auto"

def _run_job(job_id: str, path: str, platform: str) -> None:
    _jobs[job_id]["status"] = "running"
    try:
        p = Path(path)
        fn = index_directory if p.is_dir() else index_file
        new, dup = fn(path, platform)
        report = status_report(new, dup, label=p.name)
        _jobs[job_id].update({"status": "done", "new": new, "dup": dup, "report": report})
    except Exception as e:
        _jobs[job_id].update({"status": "error", "error": str(e)})

@app.post("/index-chats")
def api_index(req: IndexRequest) -> dict:
    """Startet Indexierung im Hintergrund. Antwortet sofort mit job_id."""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "queued", "path": req.path, "platform": req.platform}
    threading.Thread(target=_run_job, args=(job_id, req.path, req.platform), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}

@app.get("/job/{job_id}")
def api_job_status(job_id: str) -> dict:
    return _jobs.get(job_id, {"error": "job not found"})

@app.get("/search")
def api_search(q: str, n: int = 3) -> list:
    return search_chats(q, n)

@app.get("/stats")
def api_stats() -> dict:
    return {"collection": COLLECTION, "count": collection_size(), "chroma_path": CHROMA_PATH}

# ─── CLI ─────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(
        description="COGNITUM Chat Indexer",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--input",    help="Datei oder Verzeichnis zum Indexieren")
    ap.add_argument("--platform", default="auto",
                    choices=["auto", "claude", "chatgpt", "grok", "deepseek", "generic"])
    ap.add_argument("--query",    help="Suche in cognitum_chat_history")
    ap.add_argument("--n",        type=int, default=3, help="Anzahl Suchergebnisse")
    ap.add_argument("--stats",    action="store_true", help="Collection-Statistiken")
    ap.add_argument("--serve",    action="store_true", help="Webhook-Server starten")
    ap.add_argument("--port",     type=int, default=WEBHOOK_PORT)
    args = ap.parse_args()

    if args.input:
        p = Path(args.input).expanduser()
        print(f"Indexiere: {p}  (platform={args.platform})")
        fn = index_directory if p.is_dir() else index_file
        new, dup = fn(str(p), args.platform)
        status_report(new, dup, label=p.name)

    elif args.query:
        results = search_chats(args.query, args.n)
        print(f"\n🔍 Top {len(results)} für: \"{args.query}\"\n{'─'*60}")
        for r in results:
            m = r["metadata"]
            print(f"[{r['rank']}] dist={r['distance']:.4f} | {m.get('platform','?')} | {m.get('role','?')} | {m.get('source_file','?')}")
            print(f"    {r['content'][:300].replace(chr(10), ' ')}")
            print()

    elif args.stats:
        print(f"Collection '{COLLECTION}': {collection_size()} Chunks")
        print(f"ChromaDB: {CHROMA_PATH}")

    elif args.serve:
        print(f"Webhook auf Port {args.port}  →  POST /index-chats  |  GET /search?q=...")
        uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")

    else:
        ap.print_help()

if __name__ == "__main__":
    main()
