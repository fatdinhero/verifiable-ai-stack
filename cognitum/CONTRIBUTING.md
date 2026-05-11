# Beitragen zu COGNITUM / DaySensOS

Vielen Dank fuer dein Interesse an COGNITUM und DaySensOS. Dieses Dokument beschreibt
die Regeln und Ablaeufe fuer Beitraege zum Projekt.

## Grundregeln

### Single Source of Truth

Die Datei `governance/masterplan.yaml` ist die einzige Wahrheitsquelle fuer alle
Architekturentscheidungen, Module, Privacy-Invarianten und Normen. Aenderungen an der
Projektstruktur, Architektur oder Governance MUESSEN zuerst in dieser Datei erfolgen.
Generierte Artefakte (CLAUDE.md, AGENTS.md, docs/masterplan.md, governance/constitution.md)
duerfen NIEMALS manuell editiert werden.

### Morphologisches Entscheidungsprotokoll (Art. 14)

Jede Architektur- oder Produktentscheidung muss den morphologischen Kasten (VDI 2221)
und die Bewertungsmatrix (VDI 2225) durchlaufen. Entscheidungen werden als ADR
(Architecture Decision Record) in masterplan.yaml dokumentiert. Keine Entscheidung
ohne ADR.

### Privacy-Invarianten

Die 10 Privacy-Invarianten (PRIV-01 bis PRIV-10) sind unverletzlich. Insbesondere:

- PRIV-02/03: Kamera und Mikrofon sind default OFF (Per-Sensor-Consent)
- PRIV-06: Keine biometrischen Rohdaten in DayFeatures
- PRIV-07: PixelGuard Zero-Retention — kein Kamerabild auf Disk

Kein Beitrag darf diese Invarianten verletzen.

## Workflow

### 1. Vorbereitung

Aktuellen Masterplan lesen:
```bash
curl -sL https://gitlab.com/fatdinhero/cognitum/-/raw/main/governance/masterplan.yaml
```

Produkt-Kontext lesen:
```bash
curl -sL https://gitlab.com/fatdinhero/cognitum/-/raw/main/docs/daysensos-product-context.md
```

### 2. Entwicklung

```bash
cd ~/COS/cognitum
source .venv/bin/activate
# Aenderungen vornehmen
python -m pytest tests/ validation/tests/ -v   # 63 Tests muessen gruen sein
```

### 3. Governance-Aenderungen

Falls masterplan.yaml geaendert wurde:
```bash
python scripts/generate.py --targets all
```

### 4. Commit

Commit-Messages folgen Conventional Commits:
```
feat(daysensos): Beschreibung des Features
fix(l2): Bug in Kontextklassifikation behoben
docs: Dokumentation aktualisiert
chore(ots): OpenTimestamps-Anker hinzugefuegt
ci: Pipeline erweitert
```

### 5. Push und CI

```bash
git push origin main
```

Die GitLab CI fuehrt automatisch 4 Jobs aus:
- schema-check: Yamale + Pydantic Validierung
- consistency-test: 32 Governance-Tests
- daysensos-test: 31 Produkt-Tests
- render-configs: Artefakt-Generierung

Alle 4 Jobs MUESSEN gruen sein.

## Was NICHT gemacht werden darf

1. Generierte Dateien manuell editieren (CLAUDE.md, AGENTS.md, etc.)
2. Consent-Gate umgehen oder Kamera/Mikrofon default ON setzen
3. Cloud-Dependencies einfuehren (Local-First)
4. Gamification implementieren (Streaks, Leaderboards, Rankings)
5. LLM fuer medizinische Aussagen verwenden
6. Rohaudio speichern (nur Frequenzspektrum)
7. Kamerabilder auf Disk schreiben (PixelGuard Zero-Retention)
8. Force-Push auf main (Branch ist protected)
9. Musik-Referenzen (FatHooray, Cybersoultrap) — permanent eingestellt

## OTS-First (Art. 8)

Vor jeder Veroeffentlichung oder Version-Release MUSS ein OpenTimestamps-Stempel
gesetzt werden:

```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
git rev-parse HEAD > /tmp/commit.txt
ots stamp /tmp/commit.txt
cp /tmp/commit.txt.ots governance/ots/
```

## Lizenz

MIT License. Siehe LICENSE Datei.

## Kontakt

Fatih Dinc — https://gitlab.com/fatdinhero
