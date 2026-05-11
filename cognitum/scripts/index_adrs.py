#!/usr/bin/env python3
"""
scripts/index_adrs.py
Indexiert alle existierenden ADR-Dateien aus docs/adr/ in ChromaDB.
"""
import sys
from pathlib import Path

# Repo-Root zum Pythonpfad hinzufuegen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance.rag_memory import RAGMemory


def main():
    adr_dir = Path(__file__).resolve().parents[1] / "docs" / "adr"
    if not adr_dir.exists():
        print(f"ADR-Verzeichnis nicht gefunden: {adr_dir}")
        sys.exit(1)

    rag = RAGMemory()
    if not rag._ready:
        print("ChromaDB nicht verfuegbar — Abbruch.")
        sys.exit(1)

    adr_files = sorted(adr_dir.glob("*.md"))
    if not adr_files:
        print("Keine ADR-Dateien gefunden.")
        sys.exit(0)

    print(f"Indexiere {len(adr_files)} ADR(s) aus {adr_dir}\n")
    indexed = 0

    for filepath in adr_files:
        content = filepath.read_text(encoding="utf-8")
        adr_id = filepath.stem  # Dateiname ohne .md
        title = adr_id

        # Titel aus erster Markdown-Zeile extrahieren
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        metadata = {
            "adr_id": adr_id,
            "title": title,
            "source": str(filepath),
        }

        ok = rag.add_adr(adr_id, content, metadata)
        status = "✅" if ok else "❌"
        print(f"  {status} {adr_id}")
        if ok:
            indexed += 1

    print(f"\n{indexed}/{len(adr_files)} ADRs erfolgreich indexiert.")
    print(f"ChromaDB: {rag._adrs.count()} Dokumente in '{rag._adrs.name}'")


if __name__ == "__main__":
    main()
