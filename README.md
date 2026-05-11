# verifiable-ai-stack

**Privacy-First Wearable AI Operating System mit dezentraler semantischer Validierung und Governance**

`verifiable-ai-stack` fuehrt vier bisher getrennte Projektlinien in einem gemeinsamen Monorepo zusammen:

1. **COGNITUM** als Governance- und Produkt-SSoT fuer DaySensOS.
2. **AgentsProtocol** als Protokoll- und Validator-Schicht fuer dezentrale semantische Validierung.
3. **PoISV** als wissenschaftliche Grundlage fuer Meta-Bell Theory, Proof of WiseWork und Proof of Independent Semantic Validation.
4. **zkHalal MCP** als Compliance-Modul fuer Zero-Knowledge Sharia- und DeFi-Pruefungen.

Die gemeinsame Vision ist ein lokal kontrolliertes, privacy-first Wearable-AI-System, dessen Entscheidungen, Claims und Compliance-Pruefungen nicht nur generiert, sondern nachvollziehbar validiert, versioniert und governance-faehig gemacht werden.

## Architektur auf einen Blick

```text
Wearable / DaySensOS
  -> COGNITUM Governance
     -> masterplan.yaml, ADRs, Privacy-Invarianten, Norm-Adapter
  -> AgentsProtocol
     -> S_con, Psi, WiseScore, Rust Validator, canonical DAG
  -> PoISV Scientific Layer
     -> Meta-Bell Theory, PoWW, PoISV reference implementations
  -> zkHalal MCP
     -> Zero-Knowledge Compliance Tools
  -> Future VeriMCP
     -> gemeinsame MCP-Fassade fuer Validierung und Governance
```

## Repository-Struktur

```text
verifiable-ai-stack/
├── cognitum/                 # Governance, masterplan.yaml, DaySensOS, CNA, Generatoren
├── agentsprotocol/           # Protokoll-Implementierung, Python SDK, Rust-Validator
├── poisv/                    # Wissenschaftliche Schicht: Meta-Bell, PoWW, PoISV
├── zkhalal-mcp/              # Compliance-Tools als MCP-Server
├── mcp/                      # Platzhalter fuer zukuenftiges VeriMCP
├── docs/                     # Gemeinsame Monorepo-Dokumentation
├── .github/                  # Monorepo-CI/CD und GitHub-Metadaten
├── .gitignore                # Gemeinsame Ignore-Regeln fuer Python, Rust, Node, Daten
└── README.md                 # Diese zentrale Vision und Navigationshilfe
```

## Komponenten

| Komponente | Rolle | Wichtige Pfade |
| --- | --- | --- |
| `cognitum/` | Governance-Schicht und DaySensOS-Produktarchitektur. Enthaelt die Single Source of Truth fuer Masterplan, Privacy-Invarianten, ADRs, CNA und lokale Wearable-AI-Pipeline. | `governance/masterplan.yaml`, `scripts/generate.py`, `daysensos/`, `veriethiccore/`, `docs/adr/` |
| `agentsprotocol/` | Dezentrales semantisches Validierungsprotokoll. Kombiniert Python-Referenzimplementierung mit Rust-Validator, P2P/DAG-Komponenten und Demo-API. | `src/agentsprotocol/`, `src/validator/`, `detect/`, `schema/`, `examples/` |
| `poisv/` | Wissenschaftliche Grundlage fuer die Validierungslogik. Dokumentiert und implementiert Meta-Bell Theory, Proof of WiseWork und PoISV. | `meta-bell/`, `poww/`, `poisv/`, `notebooks/`, `proofs/` |
| `zkhalal-mcp/` | Compliance-Modul fuer Zero-Knowledge Sharia-Pruefungen ueber MCP-Tools. | `server.py`, `mcp_config.json` |
| `mcp/` | Zukuenftiger Integrationspunkt fuer VeriMCP: eine gemeinsame MCP-Fassade ueber Governance, Validierung und Compliance. | derzeit nur Platzhalter |

## Design-Prinzipien

- **Privacy-first und local-first:** Nutzerdaten bleiben lokal; Sensor-Consent, Zero-Retention und Datenminimierung sind architektonische Invarianten.
- **Verifizierbarkeit statt blosser Generierung:** Claims sollen mit semantischer Evidenz, Validator-Unabhaengigkeit und nachvollziehbarer Governance bewertet werden.
- **Governance als Code:** Architekturentscheidungen, Risiken, Normen und Produktregeln werden versioniert und testbar gehalten.
- **Dezentrale Validierung:** AgentsProtocol und PoISV liefern die Basis, um AI-Outputs gegen Korpora, Nicht-Kollusion und DAG-Ordnung zu pruefen.
- **Compliance by construction:** zkHalal und der COGNITUM Norm-Adapter zeigen, wie Compliance-Pruefungen als modulare Tools in den Stack eingebunden werden.

## Lokale Entwicklung

Jede Komponente bleibt zunaechst eigenstaendig lauffaehig. Arbeite im jeweiligen Unterordner, bis gemeinsame Build- und Release-Kommandos eingefuehrt sind.

```bash
# COGNITUM / DaySensOS
cd cognitum
python scripts/generate.py --validate-only
pytest validation/tests/ -v

# AgentsProtocol Python
cd ../agentsprotocol
pip install -e ".[dev]"
pytest tests/ -v

# AgentsProtocol Rust Validator
cd src/validator
cargo test

# PoISV
cd ../../../poisv
pip install -r requirements.txt
python -m pytest

# zkHalal MCP
cd ../zkhalal-mcp
pip install mcp pydantic
python server.py
```

## Historie und Import-Strategie

Dieses Monorepo ist historienbewusst aufgebaut:

- `cognitum` wurde aus der bisherigen Repository-Wurzel in den Prefix `cognitum/` verschoben, damit die bestehende Historie weiter ueber `git log --follow` nachvollziehbar bleibt.
- `agentsprotocol`, `poisv` und `zkhalal-mcp` wurden als `git subtree`-Imports ohne Squash in ihre jeweiligen Prefixe aufgenommen.
- Bestehender Code wurde nicht geloescht oder ueberschrieben; Konflikte wurden durch klare Prefix-Grenzen vermieden.

## Naechste Integrationsrichtung

Der erste sinnvolle Integrationspfad ist eine schmale Bruecke zwischen `cognitum` und `agentsprotocol`:

1. COGNITUM-ADRs und Masterplan-Claims als strukturierte Claims exportieren.
2. AgentsProtocol `compute_s_con`, `compute_psi` und `check_acceptance` als Validierungsstufe fuer diese Claims einsetzen.
3. Ergebnisse als Audit-Trail in `cognitum/governance/masterplan.yaml` oder separaten Governance-Reports referenzieren.
4. Danach `mcp/` als gemeinsame VeriMCP-Fassade fuer Governance-, Validation- und Compliance-Tools ausbauen.

## Lizenzhinweis

Die importierten Projekte behalten ihre jeweiligen Lizenz- und Eigentumshinweise in den Unterordnern. Dieses Root-README beschreibt die Monorepo-Struktur und ersetzt keine komponentenspezifischen Lizenzen.
