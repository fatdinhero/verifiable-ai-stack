#!/usr/bin/env python3
"""
gitops_handler.py
GitOps-Integration fuer COGNITUM Engineering Agent
Conventional Commits + MADR-4.0 ADRs + GitLab MR (urllib only)
"""
import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

GITLAB_BASE = "https://gitlab.com/api/v4"
PROJECT_PATH = "fatdinhero%2Fcognitum"  # URL-kodiert


class GitOpsHandler:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.git = ["git", "-C", str(self.repo_path)]

    # ─── Git-Hilfsmethoden ────────────────────────────────────────────────

    def _run(self, command: list) -> str:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr.strip()}")
        return result.stdout.strip()

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s-]+', '-', text).strip('-')
        return text[:50]

    def _current_branch(self) -> str:
        return self._run(self.git + ["branch", "--show-current"])

    # ─── GitLab Token ─────────────────────────────────────────────────────

    def _read_token(self) -> Optional[str]:
        """Liest GitLab-Token aus ~/.gitlab-token. Gibt None zurueck wenn fehlt."""
        token_path = Path.home() / ".gitlab-token"
        if not token_path.exists():
            return None
        token = token_path.read_text(encoding="utf-8").strip()
        return token if token else None

    # ─── Branch + ADR ─────────────────────────────────────────────────────

    def create_branch(self, feature_name: str) -> str:
        slug = self._slugify(feature_name)
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        branch_name = f"agent/{slug}-{ts}"
        self._run(self.git + ["checkout", "-b", branch_name])
        return branch_name

    def write_adr(self, feature_name: str, solution: str, score: float,
                  rationale: str, lessons: List[str]) -> Path:
        adr_dir = self.repo_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        slug = self._slugify(feature_name)
        filepath = adr_dir / f"{date_str}-{slug}.md"
        content = f"""# ADR: {feature_name}

**Datum:** {date_str}
**Status:** Vorschlag (Human Review ausstehend)
**VDI 2225 Score:** {score:.2f}

## Kontext
{feature_name}

## Entscheidung
{solution}

## Begruendung (VDI 2225)
{rationale}

## Lessons Learned
{chr(10).join(f"- {l}" for l in lessons) if lessons else "- Keine"}

---
*Generiert durch COGNITUM Engineering Agent v0.2*
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def commit_and_push(self, filepath: Path, feature_name: str, score: float) -> bool:
        try:
            adr_id = f"ADR-{datetime.utcnow().strftime('%Y-%m-%d')}"
            self._run(self.git + ["add", str(filepath)])
            commit_msg = (
                f"docs(adr): {feature_name[:60]} (Score: {score:.2f})\n\n"
                f"Refs: {adr_id}\n"
                f"Method: SPALTEN + VDI 2225"
            )
            self._run(self.git + ["commit", "-m", commit_msg])
            self._run(self.git + ["push", "-u", "origin", self._current_branch()])
            return True
        except RuntimeError as e:
            print(f"  GitOps-Warnung: {e}")
            return False

    # ─── GitLab MR via urllib ──────────────────────────────────────────────

    def create_merge_request(self, source_branch: str, title: str,
                             description: str) -> Dict[str, Any]:
        """Erstellt GitLab MR via REST API (urllib only).
        Graceful Fallback wenn Token fehlt oder API-Fehler auftritt."""
        token = self._read_token()
        if not token:
            return {
                "error": "~/.gitlab-token nicht gefunden oder leer",
                "url": None,
                "status": "skipped",
            }

        api_url = f"{GITLAB_BASE}/projects/{PROJECT_PATH}/merge_requests"
        payload = json.dumps({
            "source_branch": source_branch,
            "target_branch": "main",
            "title": title,
            "description": description,
            "labels": "agent-generated,needs-review",
            "remove_source_branch": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "PRIVATE-TOKEN": token,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "mr_iid": data.get("iid"),
                    "url": data.get("web_url"),
                    "title": data.get("title"),
                    "status": "created",
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            return {
                "error": f"HTTP {e.code}: {body[:300]}",
                "url": None,
                "status": "failed",
            }
        except Exception as e:
            return {"error": str(e), "url": None, "status": "failed"}

    # ─── Hauptmethode ─────────────────────────────────────────────────────

    def propose_adr(self, feature_name: str, solution: str, score: float,
                    rationale: str, lessons: List[str]) -> Dict[str, Any]:
        """Branch + ADR schreiben + Commit + Push + MR erstellen."""
        try:
            branch = self.create_branch(feature_name)
            filepath = self.write_adr(feature_name, solution, score, rationale, lessons)
            pushed = self.commit_and_push(filepath, feature_name, score)

            mr_result: Dict[str, Any] = {"status": "skipped", "url": None}
            if pushed:
                mr_title = f"feat(adr): {feature_name[:60]} — Score {score:.2f}"
                mr_description = self._build_mr_description(
                    feature_name, solution, score, rationale, lessons
                )
                mr_result = self.create_merge_request(branch, mr_title, mr_description)
                if mr_result.get("url"):
                    print(f"  🔗 MR erstellt: {mr_result['url']}")
                else:
                    print(f"  ⚠️  MR fehlgeschlagen: {mr_result.get('error')}")

            return {
                "branch": branch,
                "adr_path": str(filepath),
                "pushed": pushed,
                "mr_url": mr_result.get("url"),
                "mr_iid": mr_result.get("mr_iid"),
                "mr_title": f"feat(adr): {feature_name[:60]} — Score {score:.2f}",
                "mr_status": mr_result.get("status"),
                "status": "ready_for_human_review",
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def _build_mr_description(self, feature_name: str, solution: str,
                               score: float, rationale: str,
                               lessons: List[str]) -> str:
        """Baut die MR-Beschreibung aus ADR-Inhalt + Metadaten."""
        lessons_md = "\n".join(f"- {l}" for l in lessons) if lessons else "- Keine"
        return (
            f"## ADR: {feature_name}\n\n"
            f"**VDI 2225 Score:** `{score:.2f}`\n\n"
            f"### Entscheidung\n{solution}\n\n"
            f"### Begruendung (VDI 2225)\n{rationale}\n\n"
            f"### Lessons Learned\n{lessons_md}\n\n"
            f"---\n"
            f"*Generiert durch COGNITUM Engineering Agent v0.2 — "
            f"Methode: SPALTEN + VDI 2225*"
        )
