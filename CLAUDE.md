# COGNITUM — Master Kontext für Claude Code

## Eigentümer
Fatih Dinc / fatdinhero / datalabel.tech@gmail.com
Repos: github.com/fatdinhero/cognitum (privat) | gitlab.com/fatdinhero/cognitum (privat)

## Sub-Kontexte (separate Dateien)
- CLAUDE_DAYSENSOS.md — DaySensOS Wearable AI OS (Port 8111)
- CLAUDE_POISV.md — PoISV Validator (HuggingFace Space)
- CLAUDE_AGENTSPROTOCOL.md — AgentsProtocol (poisv.com)

## Meilensteinstand (Stand: 06.05.2026)
M1  ✅ MiMo Orbit genehmigt — 350M Tokens, läuft bis 28. Mai 2026
M2  ✅ gateway/sanitizer.py — Alias-Dictionary + Presidio
M3  ✅ veriethiccore/ — EU AI Act MCP Server (5 Tools, FastMCP)
M4  ⏳ Launch auf 8 MCP-Marketplaces — launch/ Texte in Arbeit
M5  ✅ spalten_agent.py läuft 24/7 — 1036+ Cases produziert
M6  ⏳ corpus/builder.py — DQM-Scoring in Arbeit
M7-M14 🔜 Graph, Fine-Tuning, Autonomes Listing

## Kritische Deadlines
28. Mai 2026 — MiMo Orbit Token-Budget läuft ab → Cases maximieren
02. Aug 2026 — EU AI Act Enforcement → VeriEthicCore Launch-Fenster

## Repo-Struktur
cognitum/
├── CLAUDE.md              ← Diese Datei (Master-Kontext)
├── CLAUDE_DAYSENSOS.md    ← DaySensOS Sub-Kontext
├── gateway/               ← M2: LiteLLM + Sanitizer
├── veriethiccore/         ← M3: EU AI Act MCP (5 Tools)
├── corpus/                ← M6: Builder + DQM
├── launch/                ← M4: Launch-Texte
├── data/
│   ├── synthetic_adrs/    ← 1036+ SPALTEN Cases (gitignored)
│   └── corpus_assets/     ← Exportierte Datasets (gitignored)
├── spalten_agent.py       ← M5: Läuft via run_loop.sh
├── governance/            ← VDI 2221, Compliance-Regeln
├── daysensos/             ← DaySensOS Server (Port 8111)
└── docs/adr/              ← Architecture Decision Records

## Sofort-Befehle
ls data/synthetic_adrs/ | wc -l          # Cases zählen
cat loop_result_*.json | python3 -m json.tool | tail -20  # Loop-Status
python3 veriethiccore/server.py stdio    # VeriEthicCore testen
python3 corpus/builder.py               # Corpus Builder ausführen
bash run_loop.sh                         # SPALTEN Loop starten
bash stop_loop.sh                        # SPALTEN Loop stoppen

## Proprietäre Aliases (NIEMALS an externe LLMs senden)
SPALTEN      → method_X7
MetaBell     → operator_psi
DQM          → metric_Q
WiseScore    → score_W
Tsirelson    → bound_T
COGNITUM     → project_C
SASKIA       → orchestrator_S
VeriEthicCore → compliance_EC
zkHalal      → compliance_ZK

## Neue Session starten
cd ~/COS/cognitum && claude --dangerously-skip-permissions
# Claude Code liest CLAUDE.md automatisch — sofort voller Kontext
