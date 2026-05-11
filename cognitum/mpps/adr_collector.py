#!/usr/bin/env python3
"""
adr_collector.py
Sammelt alle ADRs aus dem Repo
"""

import json
from pathlib import Path
from datetime import datetime

def collect_adrs(repo_path: str = ".") -> list:
    adr_dir = Path(repo_path) / "docs" / "adr"
    if not adr_dir.exists():
        return []

    adrs = []
    for file in adr_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        adrs.append({
            "id": file.stem,
            "timestamp": datetime.utcnow().isoformat(),
            "source_file": str(file),
            "content": content,
            "domain": "cna_cli",
            "quality_score": 0.85
        })
    return adrs

if __name__ == "__main__":
    adrs = collect_adrs()
    print(f"✅ {len(adrs)} ADRs gefunden")
    Path("data").mkdir(exist_ok=True)
    with open("data/collected_adrs.jsonl", "w", encoding="utf-8") as f:
        for adr in adrs:
            f.write(json.dumps(adr, ensure_ascii=False) + "\n")
    print("✅ Gespeichert unter data/collected_adrs.jsonl")
