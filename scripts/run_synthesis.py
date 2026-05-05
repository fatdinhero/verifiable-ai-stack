#!/usr/bin/env python3
"""Einmaliger oder geplanter Synthesis-Run."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from governance.synthesis_agent import SynthesisAgent

agent = SynthesisAgent()
result = agent.run()

print(f"Prinzipien destilliert: {len(result['principles'])}")
print(f"Cases analysiert: {result['total_cases_analyzed']}")
print(f"Top Domaenen: {result['top_domains']}")
print(f"Gespeichert: docs/COGNITUM_DESIGN_PRINCIPLES.md")

for p in result['principles']:
    print(f"  [{p['priority']}] {p['name']}")
