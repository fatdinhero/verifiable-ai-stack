#!/usr/bin/env python3
"""
gitops_handler.py
ADR + GitOps Integration für MPPS
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class GitOpsHandler:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.git = ["git", "-C", str(self.repo_path)]

    def _run(self, command: list) -> str:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr}")
        return result.stdout.strip()

    def create_branch(self, branch_name: str):
        self._run(self.git + ["checkout", "-b", branch_name])

    def commit_adr(self, adr_content: str, feature_name: str, score: float) -> str:
        adr_dir = self.repo_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.utcnow().strftime('%Y-%m-%d')}-{feature_name.lower().replace(' ', '-')}.md"
        filepath = adr_dir / filename
        filepath.write_text(adr_content, encoding="utf-8")
        self._run(self.git + ["add", str(filepath)])
        self._run(self.git + ["commit", "-m", f"docs(adr): {feature_name} (Score: {score:.2f})"])
        return str(filepath)

    def full_gitops_flow(self, adr_content: str, feature_name: str, score: float) -> Dict[str, Any]:
        branch_name = f"feature/{feature_name.lower().replace(' ', '-')}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        self.create_branch(branch_name)
        adr_path = self.commit_adr(adr_content, feature_name, score)
        self._run(self.git + ["push", "-u", "origin", branch_name])
        return {"branch": branch_name, "adr_path": adr_path, "status": "ready_for_review"}
