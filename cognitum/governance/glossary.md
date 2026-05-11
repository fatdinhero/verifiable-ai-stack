# COGNITUM Glossar

## Kernbegriffe
- **COS**: Civilization Operating System — uebergeordnetes Framework
- **DaySensOS**: Privacy-First Wearable AI OS (ehem. DayOS)
- **MentraOS**: Open-Source Multi-Device Variante von DaySensOS (MIT-Lizenz)
- **SSoT**: Single Source of Truth — masterplan.yaml als einzige Wahrheitsquelle
- **ADR**: Architecture Decision Record — dokumentierte Architekturentscheidung
- **CNA**: COGNITUM Norm-Adapter — generischer Compliance-Pruefadapter
- **VEC**: VeriEthicCore — ethisches Notfall-Shutdown-System fuer KI

## Module
- **L1 Perception**: 8-Kanal multimodale Sensorfusion
- **L2 Situation RuleEngine**: YAML-basierte Kontextklassifikation
- **L3 Episodes SQLite**: Temporale Segmentierung in Episoden
- **L4 Features Engineer**: Feature-Extraktion mit 14-Tage-Normalisierung
- **L5 Intelligence DayScore**: Tagesbewertung, WellnessState, Evening Coach
- **DayScore**: Aggregierter Tageswert (0-10) aus focus, energy, social, movement
- **DayFeatures**: Normalisierte Merkmale: focus, energy, social, movement
- **DayGraph**: Anonymisierter Tagesverlaufs-Export (JSON)

## Privacy & Sicherheit
- **Zero-Retention**: Keine Nutzerdaten verlassen das Geraet
- **Per-Sensor-Consent**: Jeder Sensorkanal individuell aktivierbar/deaktivierbar
- **PixelGuard**: Zero-Retention-Modul fuer Bilddaten
- **Privacy-Invariante**: Unveraenderliche Datenschutz-Eigenschaft mit definierter Testmethode
- **Consent-Gate**: Pruefmechanismus der Sensor-Einwilligung vor Datenverarbeitung
- **Consent-State**: Aktueller Einwilligungsstatus aller Sensorkanaele (Output von L1)

## Standards & Compliance
- **ISO 25010**: Software-Qualitaetsmodell (8 Characteristics, 31 Sub-Characteristics)
- **ISO 23894**: KI-Risikomanagement-Standard
- **VDI 2221/2222/2225**: Konstruktionsmethodik — morphologisches Gate
- **Morphologisches Gate**: Pflicht-Analyse nach VDI vor jeder Funktionsentscheidung
- **Morphologischer Kasten**: Systematische Loesungsraumanalyse (Zwicky-Box)
- **DSGVO**: Datenschutz-Grundverordnung (EU)
- **AAOIFI**: Accounting and Auditing Organization for Islamic Financial Institutions

## Technologie
- **zkVM-Proof**: Zero-Knowledge Virtual Machine Beweis fuer CNA-Konformitaetserklaerungen
- **MCP-Server**: Model Context Protocol Server — Schnittstelle fuer KI-Agenten
- **Ollama**: Lokaler LLM-Runner (qwen2.5:14b)
- **Jinja2**: Template-Engine fuer Artefakt-Generierung
- **Yamale**: YAML-Schema-Validierung
- **Pydantic**: Python-Datenvalidierung (Masterplan-Schema)
- **NetworkX**: Graph-Bibliothek fuer ADR/Modul-Konsistenzpruefung

## Operative Regeln
- **Golden ZIP**: Vollstaendige One-Shot-Deliverables
- **SAFE Mode**: Externes Backup vor jeder destruktiven Aktion
- **OTS-First**: OpenTimestamps-Anker vor jeder Veroeffentlichung
- **Halal-Gate**: AAOIFI 6-Faktor-Screening auf alle Revenue-Streams
- **Zakat**: 2.5% automatische Berechnung auf alle Einnahmen
