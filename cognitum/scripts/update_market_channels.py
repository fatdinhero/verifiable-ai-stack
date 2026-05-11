#!/usr/bin/env python3
"""
scripts/update_market_channels.py
Aktualisiert Revenue-Kanaele in ChromaDB via DuckDuckGo Lite + LLM.
Kann taeglich als Cron-Job oder n8n-Workflow laufen.
"""
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.market_intelligence import MarketScanner

SCAN_QUERIES = [
    ("AI dataset marketplace sell 2026",         "general"),
    ("developer plugin marketplace monetize",    "general"),
    ("MCP server marketplace AI tools",          "cognitum"),
    ("Fiverr AI gig engineering consulting",     "general"),
    ("datarade alternative data marketplace",    "general"),
]


def main() -> None:
    print(f"\n{'='*60}")
    print(f"Market Channel Updater — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"{'='*60}\n")

    scanner = MarketScanner()

    # Seed (idempotent — ueberspringt bekannte Kanaele)
    print("Seeding bekannte Kanaele...")
    scanner.seed_known_channels()

    before = scanner._col.count() if scanner._ready else 0
    print(f"Kanaele vor Scan: {before}\n")

    total_new = 0
    for query, domain in SCAN_QUERIES:
        print(f"Scan: '{query}' (domain={domain})")
        try:
            found = scanner.scan(domain=domain, query=query)
            print(f"  → {len(found)} neue/aktualisierte Kanaele")
            total_new += len(found)
            for ch in found:
                print(f"     + {ch.get('name', '?')} | {ch.get('price_range', '?')} | score={ch.get('confidence_score', '?')}")
        except Exception as e:
            print(f"  ⚠️  Fehler: {e}")

    after = scanner._col.count() if scanner._ready else 0

    print(f"\n{'='*60}")
    print(f"Zusammenfassung:")
    print(f"  Kanaele vorher : {before}")
    print(f"  Kanaele nachher: {after}")
    print(f"  Neu/aktualisiert via Scan: {total_new}")
    print(f"{'='*60}\n")

    # Abschliessende Ausgabe aller Kanaele
    channels = scanner.get_channels_for_domain("general", max_age_days=365)
    print(f"Alle gespeicherten Kanaele ({len(channels)}):")
    for c in channels:
        print(
            f"  [{c.get('confidence_score', 0):.2f}] {c.get('name', '?'):<30} "
            f"| {c.get('price_range', '?'):<20} | {c.get('revenue_speed', '?')}"
        )


if __name__ == "__main__":
    main()
