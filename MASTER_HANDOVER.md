# COGNITUM — Master Handover Dokument
**Stand:** 07.05.2026  
**Eigentümer:** Fatih Dinc (fatdinhero / datalabel.tech@gmail.com)  
**Repos:** gitlab.com/fatdinhero/cognitum (primary) | github.com/fatdinhero/cognitum (mirror)

---

## 1. Projektübersicht

COGNITUM ist ein AI-Engineering-Ökosystem, das drei Kernprodukte verbindet:

| Produkt | Beschreibung | Status |
|---|---|---|
| **DaySensOS** | Privacy-First Wearable AI OS (Port 8111) | Aktiv, L1–L5 implementiert |
| **VeriEthicCore** | EU AI Act Compliance MCP Server (5 Tools) | ✅ M3 abgeschlossen |
| **PoISV / AgentsProtocol** | Validator + Protokoll (poisv.com) | In Entwicklung |

Der autonome Loop (`spalten_agent.py`) produziert seit M5 kontinuierlich ADR-Cases. Stand 07.05.2026: **1424 Cases** in `data/synthetic_adrs/`.

---

## 2. Meilensteinstand

| # | Meilenstein | Status | Details |
|---|---|---|---|
| M1 | MiMo Orbit genehmigt | ✅ | 350M Tokens, läuft bis **28. Mai 2026** |
| M2 | gateway/sanitizer.py | ✅ | Alias-Dictionary + Presidio PII-Schutz |
| M3 | veriethiccore/ EU AI Act MCP | ✅ | 5 Tools, FastMCP, stdio-Transport |
| M4 | Launch auf 8 MCP-Marketplaces | ⏳ | `launch/` Texte in Arbeit |
| M5 | spalten_agent.py 24/7 | ✅ | 1424+ Cases produziert |
| M6 | corpus/builder.py DQM-Scoring | ⏳ | Builder läuft, Scoring in Arbeit |
| M7–M14 | Graph, Fine-Tuning, Autonomes Listing | 🔜 | Geplant nach M6 |

---

## 3. Kritische Deadlines

```
28. Mai 2026  — MiMo Orbit Token-Budget läuft ab
                → PRIORITÄT: Cases maximieren, Loop am Laufen halten
                → Verbleibende Zeit: ~21 Tage

02. Aug 2026  — EU AI Act Enforcement
                → PRIORITÄT: VeriEthicCore (M3) auf Marketplaces deployen (M4)
                → Launch-Fenster: Juni/Juli 2026
```

---

## 4. Repo-Struktur

```
cognitum/
├── CLAUDE.md                    # Master-Kontext für Claude Code
├── CLAUDE_DAYSENSOS.md          # DaySensOS Sub-Kontext
├── CLAUDE_POISV.md              # PoISV Sub-Kontext
├── CLAUDE_AGENTSPROTOCOL.md     # AgentsProtocol Sub-Kontext
├── gateway/                     # M2: LiteLLM + Sanitizer (Presidio)
├── veriethiccore/               # M3: EU AI Act MCP Server
│   └── server.py                # FastMCP, 5 Tools, stdio
├── corpus/                      # M6: Builder + DQM-Scoring
│   └── builder.py
├── launch/                      # M4: Launch-Texte für Marketplaces
├── daysensos/                   # DaySensOS Server (Port 8111)
├── daysensos-app/               # Frontend / API-Client
├── data/
│   ├── synthetic_adrs/          # 1424+ SPALTEN Cases (gitignored)
│   ├── training/                # SFT + DPO Datasets
│   └── corpus_assets/           # Exportierte Datasets (gitignored)
├── governance/                  # VDI 2221, Compliance-Regeln, masterplan.yaml
├── docs/
│   ├── adr/                     # Architecture Decision Records
│   ├── COGNITUM_DESIGN_PRINCIPLES.md   # Auto-destilliert aus ADRs
│   └── design_principles.json
├── spalten_agent.py             # M5: Autonomer Case-Generator
├── run_loop.sh / stop_loop.sh   # Loop-Steuerung
└── tests/                       # Test-Suite
```

---

## 5. DaySensOS — Architektur

DaySensOS implementiert eine 5-Layer Privacy-First Sensorfusion:

```
L1 Perception   → 8-Kanal Sensorfusion mit Consent-Gate
L2 Situation    → YAML-Regelwerk Kontextklassifikation (RF-Classifier)
L3 Episodes     → SQLite temporale Segmentierung, 3-Kontext-Buffer
L4 Features     → 14-Tage relative Normalisierung (focus, energy, social, movement)
L5 Intelligence → DayScore (0–10), WellnessState, Recommendations
```

**API-Endpunkte (Port 8111):**
- `POST /capture` — Sensordaten empfangen, L1–L5 verarbeiten
- `GET /status` — Health-Check + Tagesstand
- `GET /episodes/today` — Heutige Episoden
- `GET /score` — Aktueller DayScore

**Inviolable Rules (nie brechen):**
1. Kamera + Mikrofon DEFAULT OFF (PRIV-02/03)
2. Zero-Retention: Kein Kamerabild auf Disk (PixelGuard)
3. Kein Rohaudio: Nur Frequenzspektrum
4. Keine Gamification (RISK-04)
5. Kein LLM für medizinische Aussagen (RISK-05)
6. Keine biometrischen Rohdaten in DayFeatures (PRIV-06)
7. Local-First — keine Cloud-Abhängigkeit
8. Morphologisches Gate vor jeder Entscheidung (EU AI Act Art. 14)

---

## 6. SPALTEN Loop — Autonomer Case-Generator

Der SPALTEN-Agent läuft 24/7 und generiert Architecture Decision Records nach der SPALTEN-Methode:

**Sofort-Befehle:**
```bash
bash run_loop.sh              # Loop starten
bash stop_loop.sh             # Loop stoppen
ls data/synthetic_adrs/ | wc -l  # Cases zählen (aktuell: 1424)
cat loop_result_*.json | python3 -m json.tool | tail -20  # Status
```

**Aktueller Loop-Stand (05.05.2026):**
- Letzte bekannte Iterationen: RISK-07 (Bus-Faktor), RISK-02 (RF-Classifier Diskriminierung)
- Confidence-Score: ~0.72
- Problem-Bibliothek: 110 Seeds, 10 Domains, marktrelevant
- ChromaDB-Rauschen: unterdrückt (fix a751c50)

---

## 7. Design Principles (auto-destilliert)

Stand 06.05.2026: 10 Prinzipien aus 1357 ADR-Cases, Domains: `eu_ai_act`, `daysensos`

| Priorität | Prinzip |
|---|---|
| CRITICAL | Automatische Dokumentation |
| CRITICAL | Sicherheit durch Segregation |
| HIGH | Protobuf für Datenformatierung |
| HIGH | Automatisches Logging |
| HIGH | Semver für Versionierung |
| MEDIUM | REST API Design |

Vollständige Liste: `docs/COGNITUM_DESIGN_PRINCIPLES.md`

---

## 8. VeriEthicCore — EU AI Act MCP

```bash
python3 veriethiccore/server.py stdio   # Testen
```

5 MCP-Tools implementiert. Ziel-Deployment: 8 MCP-Marketplaces bis August 2026.

---

## 9. Gateway / Sanitizer

`gateway/sanitizer.py` schützt proprietäre Methodennamen via:
- Alias-Dictionary (SPALTEN → method_X7 etc.)
- Presidio PII-Erkennung

**Aliases — NIEMALS an externe LLMs senden:**
```
SPALTEN       → method_X7
MetaBell      → operator_psi
DQM           → metric_Q
WiseScore     → score_W
Tsirelson     → bound_T
COGNITUM      → project_C
SASKIA        → orchestrator_S
VeriEthicCore → compliance_EC
zkHalal       → compliance_ZK
```

---

## 10. Offene Punkte & Nächste Schritte

1. **[URGENT – 28.05]** Loop am Laufen halten, Cases maximieren vor MiMo-Ablauf
2. **[URGENT – 28.05]** corpus/builder.py DQM-Scoring abschließen (M6)
3. **[JUNI]** launch/ Texte für 8 MCP-Marketplaces fertigstellen (M4)
4. **[JUNI/JULI]** VeriEthicCore auf Marketplaces deployen
5. **[NACH M6]** Graph-Integration (M7), Fine-Tuning (M8), Autonomes Listing (M9+)
6. `daysensos-app/src/network/api.ts` — uncommitted changes prüfen
7. `data/training/` SFT + DPO Datasets — uncommitted changes committen

---

## 11. Session starten

```bash
cd ~/COS/cognitum && claude --dangerously-skip-permissions
# Claude Code liest CLAUDE.md automatisch — sofort voller Kontext
```
