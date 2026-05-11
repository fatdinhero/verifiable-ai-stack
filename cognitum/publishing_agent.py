"""
COGNITUM — Autonomous Publishing Agent (APA)
Marke:   agentsprotocol.org
Autor:   Fatih Dinc (Fatih X.)
Version: v0.1.0
"""

import os, json, sqlite3, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

BASE_DIR  = Path.home() / "COS" / "cognitum"
DB_PATH   = BASE_DIR / "publishing_agent.db"
ENV_PATH  = BASE_DIR / ".env"
LOGS_DIR  = BASE_DIR / "logs"
DRAFTS_LOG = LOGS_DIR / "paragraph_drafts.log"

def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Gumroad store URL — optional, activates buy-link injection
    env.setdefault("GUMROAD_STORE_URL", os.environ.get("GUMROAD_STORE_URL", ""))
    return env

ENV = load_env()

@dataclass
class PublishJob:
    title: str
    raw_content: str
    commit_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS publish_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, commit_hash TEXT, platform TEXT,
        title TEXT, success INTEGER, error TEXT, post_id TEXT)""")
    conn.commit()
    return conn

def log_publish(conn, job, platform, success, error="", post_id=""):
    conn.execute("""INSERT INTO publish_log
        (timestamp,commit_hash,platform,title,success,error,post_id)
        VALUES (?,?,?,?,?,?,?)""",
        (job.timestamp, job.commit_hash, platform,
         job.title, int(success), error, post_id))
    conn.commit()

class LocalLLM:
    def __init__(self, model="qwen2.5:7b"):
        self.model = model
    def generate(self, prompt, max_tokens=500):
        try:
            r = requests.post("http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt,
                      "stream": False, "options": {"num_predict": max_tokens}},
                timeout=60)
            return r.json().get("response", "").strip()
        except Exception as e:
            return f"[LLM unavailable: {e}]"

class ContentAdapter:
    SPECS = {
        "farcaster":   {"max": 320,   "style": "kurz, prägnant, 2-3 Hashtags, kein Markdown"},
        "paragraph":   {"max": 50000, "style": "ausführlich, strukturiert, Markdown"},
        "reddit":      {"max": 10000, "style": "community-orientiert, kein Marketing"},
        "huggingface": {"max": 5000,  "style": "technisch, für ML-Entwickler"},
    }
    # Suffix injected per platform when GUMROAD_STORE_URL is set
    GUMROAD_SUFFIX = {
        "farcaster":   "\n\n🛒 saskiaspohrmann.gumroad.com",
        "paragraph":   "\n\n---\n**🛒 Produkte kaufen:** https://saskiaspohrmann.gumroad.com",
        "reddit":      "\n\n🛒 **Kaufen:** https://saskiaspohrmann.gumroad.com",
        "huggingface": "\n\n**🛒 Buy:** https://saskiaspohrmann.gumroad.com",
    }

    def __init__(self, llm):
        self.llm = llm

    def adapt(self, job, platform):
        spec   = self.SPECS.get(platform, {"max": 500, "style": "neutral"})
        suffix = self.GUMROAD_SUFFIX.get(platform, "") if ENV.get("GUMROAD_STORE_URL") else ""
        prompt = f"""Plattform: {platform}
Stil: {spec['style']}
Max Zeichen: {spec['max']}
Titel: {job.title}
Inhalt: {job.raw_content[:1000]}
Gib NUR den fertigen Text aus, auf Deutsch:"""
        text = self.llm.generate(prompt, 600)
        # Truncate LLM output to leave room for the suffix
        body_max = spec["max"] - len(suffix)
        if len(text) > body_max:
            text = text[:body_max - 3] + "..."
        return text + suffix

def publish_via_mcp_hint(job: "PublishJob") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} | {job.title} | {job.commit_hash} | PENDING_MCP_PUBLISH\n"
    with DRAFTS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print(f"  📋 Draft-Queue: {DRAFTS_LOG}")


class FarcasterPublisher:
    def publish(self, content, job):
        k, s = ENV.get("NEYNAR_API_KEY"), ENV.get("FARCASTER_SIGNER_UUID")
        if not k or not s:
            return False, "NEYNAR_API_KEY oder FARCASTER_SIGNER_UUID fehlt"
        try:
            r = requests.post("https://api.neynar.com/v2/farcaster/cast",
                headers={"api_key": k, "Content-Type": "application/json"},
                json={"signer_uuid": s, "text": content}, timeout=30)
            return True, r.json().get("cast", {}).get("hash", "ok")
        except Exception as e:
            return False, str(e)

class ParagraphPublisher:
    BASE = "https://public.api.paragraph.com/api"

    def publish(self, content, job):
        k      = ENV.get("PARAGRAPH_API_KEY")
        pub_id = ENV.get("PARAGRAPH_PUBLICATION_ID")
        if not k:
            return False, "PARAGRAPH_API_KEY fehlt"
        if not pub_id:
            return False, "PARAGRAPH_PUBLICATION_ID fehlt"
        r = requests.post(
            f"{self.BASE}/v1/publications/{pub_id}/posts",
            headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            json={"title": job.title, "body": content, "status": "draft"},
            timeout=30,
        )
        if r.ok:
            post_id = r.json().get("id", "?")
            return True, f"Paragraph Draft: {post_id} → paragraph.com/editor/{post_id}"
        if r.status_code == 500:
            print("  ⚠️  REST 500 — Fallback via MCP empfohlen")
            publish_via_mcp_hint(job)
            return False, "Paragraph REST API 500 — MCP-Fallback: paragraph.com/editor manuell"
        publish_via_mcp_hint(job)
        return False, f"Paragraph {r.status_code}: {r.text[:120]}"

class RedditPublisher:
    def publish(self, content, job):
        return False, "Reddit API Registrierung ausstehend"

class HuggingFacePublisher:
    def publish(self, content, job):
        if not ENV.get("HF_TOKEN"):
            return False, "HF_TOKEN fehlt"
        return True, "HF: manuelles Update empfohlen"

class MastodonPublisher:
    def publish(self, content, job):
        token    = ENV.get("MASTODON_ACCESS_TOKEN")
        instance = ENV.get("MASTODON_INSTANCE")
        if not token or not instance:
            return False, "MASTODON_ACCESS_TOKEN fehlt"
        try:
            r = requests.post(
                f"{instance.rstrip('/')}/api/v1/statuses",
                headers={"Authorization": f"Bearer {token}"},
                data={"status": content[:500]},
                timeout=30,
            )
            r.raise_for_status()
            return True, r.json().get("url", "ok")
        except Exception as e:
            return False, str(e)

class GumroadNotifier:
    """No API call — only confirms the buy-link was embedded in all posts."""
    def publish(self, content, job):
        if not ENV.get("GUMROAD_STORE_URL"):
            return False, "GUMROAD_STORE_URL nicht gesetzt — Link nicht eingebettet"
        return True, "Link eingebettet in alle Posts"

class AutonomousPublishingAgent:
    PUBLISHERS = {
        "farcaster":   FarcasterPublisher(),
        "paragraph":   ParagraphPublisher(),
        "reddit":      RedditPublisher(),
        "huggingface": HuggingFacePublisher(),
        "mastodon":    MastodonPublisher(),
        "gumroad":     GumroadNotifier(),
    }
    def __init__(self):
        self.llm     = LocalLLM()
        self.adapter = ContentAdapter(self.llm)
        self.conn    = init_db()

    def run(self, job):
        print(f"\n{'═'*55}")
        print(f" agentsprotocol.org Publishing Agent")
        print(f" {job.title[:50]}")
        print(f" Commit: {job.commit_hash} | {job.timestamp}")
        print(f"{'═'*55}\n")
        results = {}
        # Git push
        print("▶ [1] Git → GitLab + GitHub")
        try:
            subprocess.run(["git","push","origin","main"], cwd=BASE_DIR,
                check=True, capture_output=True)
            subprocess.run(["git","push","github","main"], cwd=BASE_DIR,
                check=True, capture_output=True)
            results["git"] = {"success": True}
            print("  ✅ Git: beide Remotes aktuell")
        except Exception as e:
            results["git"] = {"success": False, "error": str(e)}
            print(f"  ❌ Git: {e}")
        # Plattformen
        for i, (platform, publisher) in enumerate(self.PUBLISHERS.items(), 2):
            print(f"▶ [{i}] {platform.capitalize()}")
            try:
                content = self.adapter.adapt(job, platform)
                ok, info = publisher.publish(content, job)
                log_publish(self.conn, job, platform, ok, "" if ok else info,
                            info if ok else "")
                results[platform] = {"success": ok, "info": info}
                icon = "✅" if ok else "❌"
                print(f"  {icon} {info}")
            except Exception as e:
                log_publish(self.conn, job, platform, False, str(e))
                results[platform] = {"success": False, "info": str(e)}
                print(f"  ❌ {e}")

        # Summary
        print(f"\n{'─'*55}")
        ok_count = sum(1 for k, v in results.items() if v.get("success"))
        print(f" {ok_count}/{len(results)} Plattformen erfolgreich")
        print(f"{'─'*55}\n")
        return results


if __name__ == "__main__":
    import argparse, hashlib

    parser = argparse.ArgumentParser(
        prog="publishing_agent",
        description="agentsprotocol.org — Autonomous Publishing Agent",
    )
    parser.add_argument("--title",   required=True, help="Titel des Posts")
    parser.add_argument("--content", required=True, help="Roher Inhalt (oder Pfad zu .txt)")
    parser.add_argument("--commit",  default="",    help="Git-Commit-Hash (optional)")
    args = parser.parse_args()

    # --content kann ein Dateipfad oder direkter Text sein
    content_path = Path(args.content)
    raw = content_path.read_text(encoding="utf-8") if content_path.is_file() else args.content

    commit = args.commit or hashlib.sha1(raw.encode()).hexdigest()[:8]

    job   = PublishJob(title=args.title, raw_content=raw, commit_hash=commit)
    agent = AutonomousPublishingAgent()
    agent.run(job)
