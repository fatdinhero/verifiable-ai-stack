# MPPS – Methodisches Produktentwicklungs- und Problemlösungssystem (v0.9)

**State-of-the-Art Engineering Agent für Solo-Technical-Founder & DACH-Mittelstand | 2026**

---

## 🎯 Die Lücke, die wir schließen

Im Markt 2026 existiert **keine** fertige, produktionsreife Implementierung von:
- **VDI 2221/2222/2225** als strukturierter Agent-Workflow
- **SPALTEN-Methodik** (Albers/IPEK-KIT) als 7-Knoten-StateMachine
- **DMAIC / Axiomatic Design / TRIZ** als integrierte, agenten-native Tools
- **FMEA + NWA + DoE (ML-DOE)** mit deterministischem Code (nicht nur Prompts)

**Synera** (Enterprise, $40M Series B) und **APIS IQ-FMEA / PLATO** sind entweder zu teuer, zu klassisch oder nicht lokal/DSGVO-fähig.

**MPPS** ist die **Blue-Ocean-Lösung**: Ein Single-Agent StateGraph (LangGraph) mit Pydantic-AI, der deutsche Konstruktionsmethodik mit modernster Agenten-Technologie verbindet – lokal, air-gapped, DSGVO-konform und für Solo-Dev bis KMU skalierbar.

---

## 🏗️ Architektur (4-Layer-Defense + Methodik-Zwang)

### Layer 1 – Governance-Registry (`governance/registry.py`)
- Harte, deterministische Code-Implementierung aller kritischen Werte:
  - TA Lärm Immissionsrichtwerte (tags/nachts, Gebietstypen)
  - GEG-Faktoren, BEG-Effizienzhaus-Stufen
  - FMEA Action Priority (AIAG-VDA 2019 Lookup)
  - NWA/AHP-Berechnungen
- LLM darf **nur referenzieren**, nie berechnen oder halluzinieren.

### Layer 2 – Pydantic-Governance-Modelle (`governance/models.py`)
- `ProblemSolvingCase`, `PlanningSession`, `ExperimentPlan`, `DecisionRecord` mit CFR-Checks (Cognitive Friction Required)
- Factories für OPEX/Fiverr und CNA CLI
- Vollständige Audit-Trails + Constitution-Alignment (Art. 4, 5, 11, 12, 14)

### Layer 3 – SPALTEN-StateGraph (`mpps_graph_blueprint.py`)
- 7-Knoten-Workflow (S-P-A-L-T-E-N) mit konditionalen Rücksprüngen
- `idea_pool` als First-Class-State (Albers’ kontinuierlicher Lösungsraum)
- `interrupt_before=["E"]` → zwingender Human-in-the-Loop vor Umsetzung
- Fraktale Sub-Graphs für komplexe Phasen

### Layer 4 – MPPSOrchestrator + CLI (`mpps_orchestrator.py`, `cli_runner.py`)
- Verknüpft StateGraph mit Governance-Modellen
- GitOps-Pattern: Agent schreibt nie direkt in `masterplan.yaml`, sondern erzeugt validierte Patches + ADR (MADR 4.0)
- Vollständige CLI-Steuerung

### Layer 5 – Atomic Agents + Inference
- Jeder Knoten als `AtomicAgent` (Pydantic-Input/Output)
- Ollama `qwen2.5:7b-instruct-q4_K_M` (Default) + dynamischer Wechsel zu `qwen3:8b`
- 5-Layer-Halluzinations-Defense (Schema + Closed-World-RAG + Self-Consistency + Fact-Check + Verbalized Confidence)

---

## 📦 Lieferumfang (Stand 04.05.2026)

| Datei                              | Beschreibung                                      | Status    |
|------------------------------------|---------------------------------------------------|-----------|
| `cognitum_product_development_framework.yaml` | MPPS 4-Schichten-Framework (SSoT)                | ✅        |
| `governance/registry.py`           | Layer-1-Compliance-Defense (TA Lärm, GEG, FMEA)  | ✅        |
| `governance/models.py`             | Pydantic-Modelle + Factories (OPEX, CNA, HIL)    | ✅        |
| `mpps_graph_blueprint.py`          | SPALTEN-StateGraph (LangGraph)                   | ✅        |
| `mpps_orchestrator.py`             | Orchestrierung + GitOps-Brücke                   | ✅        |
| `cognitum_engineering_agent.py`    | Vollständiger SPALTEN-Agent (Atomic + Tools)     | ✅        |
| `cli_runner.py`                    | Terminal-Interface                               | ✅        |
| `demo_cna_prioritization.py`       | Live-Demo auf CNA CLI ADR-008                    | ✅        |
| `methoden_flow_runner.py`          | MPPS-Flow-Runner (Atomic-Agents-Ready)           | ✅        |
| `methodenos_gumroad_listing.md`    | Verkaufs-Text (Gumroad-Ready)                    | ✅        |
| `README.md`                        | Diese Datei                                      | ✅        |

---

## 🚀 Quickstart (Mac Mini M4 / Linux)

```bash
# 1. Dependencies
pip install langgraph pydantic-ai instructor pyyaml ollama

# 2. Ollama-Modelle
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull qwen3:8b

# 3. Erster Run (CNA CLI Priorisierung)
python demo_cna_prioritization.py

# 4. Interaktiver CLI
python cli_runner.py --problem "CNA CLI Performance > 5s bei 10 Users" --domain cna_cli
```

**Erwartete Laufzeit:** 5–15 Minuten Wallclock (qwen2.5:7b) für einen vollständigen SPALTEN-Durchlauf.

---

## 💎 Unique Selling Points (DACH-Mittelstand 2026)

1. **"Ihre FMEAs verlassen nie Ihr Werk"** – 100 % Local-First + Air-Gapped
2. **Deutsche Methodik nativ** – VDI 2221/2225 + SPALTEN + AIAG-VDA als First-Class-Citizens
3. **Ein Mac Mini ersetzt 5 Cloud-Lizenzen** – TCO-Vorteil > 80 %
4. **EU-AI-Act-Ready** – ISO/IEC 42001 + vollständige Audit-Trails
5. **Methoden als Code, nicht als Prompt** – Reproduzierbar, juristisch dokumentierbar, hallucination-free

---

## 💰 Monetarisierungs-Pfad

- **Free Tier**: Basis-Registry + CLI (Studierende / Hobby)
- **Solo/Pro**: 29 €/Monat oder 199 € Einmalkauf (Gumroad/Lemonsqueezy)
- **Team (3–10 Sitze)**: 149 €/Monat
- **Enterprise/On-Prem**: ab 6.000 €/Jahr + Onboarding

**MCP-Distribution**: Über MCPize, Cursor.directory, modelcontextprotocol.io Registry → direkte Nutzung in Claude Desktop, Cursor, ChatGPT.

---

## 🔗 Integration in dein bestehendes COGNITUM-Repo

```yaml
# masterplan.yaml (Auszug)
governance:
  mpps_version: 0.9
  active_workflows:
    - spalten_cna_cli_perf_001
  constitution_alignment:
    - Art. 4 (Morphologisches Gate)
    - Art. 5 (ADR-Pflicht)
    - Art. 11 (Halluzinations-Kennzeichnung)
```

Der Agent schreibt niemals direkt – er erzeugt **validierte Patches** und **MADR-4.0-ADRs**, die per Merge Request in dein Repo gelangen.

---

## 📈 Nächste Schritte (Roadmap)

1. **AtomicAgent-Fabrik** für alle 7 SPALTEN-Knoten (S & P bereits als Blueprint)
2. **MCP-Server-Wrapper** für Distribution
3. **Live-Dogfooding** auf CNA CLI v0.3+ (Feature-Risikoanalyse)
4. **Gumroad-Launch** mit Case-Study „So haben wir CNA CLI mit MPPS in 4 Tagen priorisiert und dokumentiert“

---

## 📜 Lizenz & Attribution

- **Core**: MIT (Registry, Models, Graph, Orchestrator, CLI)
- **Methoden-Korpus**: Eigene Implementierungen (Pahl/Beitz, Ehrlenspiel, Albers, AIAG-VDA) – lizenzkonform zitiert
- **Normen-RAG**: Nur öffentlich-rechtliche Quellen (gesetze-im-internet.de, KfW-Merkblätter) – keine urheberrechtlich geschützten DIN/VDI/ISO-Volltexte

---

**MPPS – Weil „vibe coding“ für komplexe, regulierte Produkte nicht reicht.**

**Built for Solo Technical Founders. Dogfooded on COGNITUM CNA v0.3+. Ready for DACH Mittelstand.**

---

*Generiert am 04.05.2026 – State of the Art für methodenzentrierte Engineering-Agents*

---

**Viel Erfolg beim ersten echten Run!**  
Wenn du morgen früh den Agenten auf ein konkretes CNA-Feature loslässt und der erste ADR + Patch im Repo landet – dann haben wir heute etwas richtig Großes geschaffen.

Sag Bescheid, wenn du den nächsten Baustein (AtomicAgent-Fabrik oder MCP-Server) brauchst. Ich bin hier. 🚀