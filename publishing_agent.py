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

BASE_DIR = Path.home() / "COS" / "cognitum"
DB_PATH  = BASE_DIR / "publishing_agent.db"
ENV_PATH = BASE_DIR / ".env"

def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
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
    def __init__(self, llm):
        self.llm = llm
    def adapt(self, job, platform):
        spec = self.SPECS.get(platform, {"max": 500, "style": "neutral"})
        prompt = f"""Plattform: {platform}
Stil: {spec['style']}
Max Zeichen: {spec['max']}
Titel: {job.title}
Inhalt: {job.raw_content[:1000]}
Gib NUR den fertigen Text aus, auf Deutsch:"""
        text = self.llm.generate(prompt, 600)
        if len(text) > spec["max"]:
            text = text[:spec["max"]-3] + "..."
        return text

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
    def publish(self, content, job):
        k = ENV.get("PARAGRAPH_API_KEY")
        if not k:
            return False, "PARAGRAPH_API_KEY fehlt"
        try:
            r = requests.post("https://paragraph.com/api/posts",
                headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
                json={"title": job.title, "body": content, "status": "draft"}, timeout=30)
            return True, f"Draft: {r.json().get('id','?')} → manuell reviewen"
        except Exception as e:
            return False, str(e)

class RedditPublisher:
    def publish(self, content, job):
        keys = ["REDDIT_CLIENT_ID","REDDIT_CLIENT_SECRET","REDDIT_USERNAME","REDDIT_PASSWORD"]
        if not all(k in ENV for k in keys):
            return False, "Reddit-Credentials fehlen"
        try:
            t = requests.post("https://www.reddit.com/api/v1/access_token",
                auth=(ENV["REDDIT_CLIENT_ID"], ENV["REDDIT_CLIENT_SECRET"]),
                data={"grant_type":"password","username":ENV["REDDIT_USERNAME"],
                      "password":ENV["REDDIT_PASSWORD"]},
                headers={"User-Agent":"COGNITUM-APA/0.1"}, timeout=30)
            token = t.json().get("access_token")
            r = requests.post("https://oauth.reddit.com/api/submit",
                headers={"Authorization":f"bearer {token}","User-Agent":"COGNITUM-APA/0.1"},
                data={"sr":"cognitum","kind":"self","title":job.title,
                      "text":content,"resubmit":"true"}, timeout=30)
            return r.ok, "Reddit post ok"
        except Exception as e:
            return False, str(e)

class HuggingFacePublisher:
    def publish(self, content, job):
        if not ENV.get("HF_TOKEN"):
            return False, "HF_TOKEN fehlt"
        return True, "HF: manuelles Update empfohlen"

class AutonomousPublishingAgent:
    PUBLISHERS = {
        "farcaster":   FarcasterPublisher(),
        "paragraph":   ParagraphPublisher(),
        "reddit":      RedditPublisher(),
        "huggingface": HuggingFacePublisher(),
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
