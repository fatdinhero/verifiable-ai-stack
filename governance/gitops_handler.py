#!/usr/bin/env python3
"""
gitops_handler.py
GitOps-Integration fuer COGNITUM Engineering Agent
Conventional Commits + MADR-4.0 ADRs + GitLab MR (optional)
"""
import os, re, subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class GitOpsHandler:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.git = ["git", "-C", str(self.repo_path)]

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

    def create_branch(self, feature_name: str) -> str:
        slug = self._slugify(feature_name)
        date_str = datetime.utcnow().strftime("%Y%m%d")
        branch_name = f"agent/{slug}-{date_str}"
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
            self._run(self.git + ["push", "-u", "origin",
                                   self._run(self.git + ["branch", "--show-current"])])
            return True
        except RuntimeError as e:
            print(f"  GitOps-Warnung: {e}")
            return False

    def propose_adr(self, feature_name: str, solution: str, score: float,
                    rationale: str, lessons: List[str]) -> Dict[str, Any]:
        """Hauptmethode: Branch + ADR + Commit + Push"""
        try:
            branch = self.create_branch(feature_name)
            filepath = self.write_adr(feature_name, solution, score, rationale, lessons)
            pushed = self.commit_and_push(filepath, feature_name, score)
            return {
                "branch": branch,
                "adr_path": str(filepath),
                "pushed": pushed,
                "mr_title": f"feat(adr): {feature_name[:60]} — Score {score:.2f}",
                "status": "ready_for_human_review"
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
