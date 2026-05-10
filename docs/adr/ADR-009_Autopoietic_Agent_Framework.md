# ADR-009: COGNITUM → Autopoietic Agent Framework

**Status:** PROPOSED  
**Datum:** 2026-05-10  
**Autor:** Fatih Dinc  
**Revenue-Gate:** Implementierung beginnt erst nach erstem Gumroad-Revenue  

---

## Kontext

COGNITUM v0.9.0 ist ein funktionsfähiges Pipeline-System (L1–L5, FastAPI, CNA CLI).
Der Autonomous Loop (autonomous_loop.py) läuft bereits, ist aber nicht formal als
Agenten-Framework modelliert. ADR-008 hat CNA CLI als erste Monetarisierungs-
priorität gesetzt. Nach erstem Revenue soll COGNITUM zu einem vollständigen
autopoietischen Agenten-Framework ausgebaut werden.

---

## Entscheidung

COGNITUM wird nach Revenue-Gate zu einem Autopoietic Agent Framework erweitert.
Die Zielstruktur trennt Runtime, Agenten, Governance, Memory, Autopoiesis,
Audit und API in eigenständige Module.

---

## Zielstruktur            cognitum_core/          Runtime-Kernel
cognitum_agents/        BaseAgent, AgentRegistry
cognitum_governance/    PolicyEngine (CNA erweitert auf Agenten)
cognitum_memory/        MemoryStore (SQLite + SQLCipher — schließt RISK-03)
cognitum_autopoiesis/   AutopoiesisEngine (formalisierter Loop)
cognitum_audit/         AuditLogger, Golden ZIP
cognitum_api/           FastAPI refaktoriert
cognitum_theory/        Platzhalter für IP-Module (DPMA-gesperrt)           **MVP-Definition:** 1 Agent, 1 Task, 1 Policy Check, 1 Memory Write,
1 Audit Entry, 1 Score — vollständig durchlaufend.

---

## Konsequenzen

**Positiv:**
- Formalisiert den bestehenden Loop als reproduzierbares Framework
- Schließt RISK-03 (SQLCipher) als Teil der Memory-Implementierung
- Basis für NGI0-Antrag und Framework-Monetarisierung

**Negativ / Risiken:**
- Erheblicher Refactoring-Aufwand
- Bus-Faktor bleibt 1 (RISK-07)

---

## Abgrenzung zu bestehenden ADRs

| ADR | Verhältnis |
|-----|------------|
| ADR-004 | CNA MCP-Server wird in cognitum_governance/ integriert |
| ADR-005 | Consent-Gate wird in cognitum_agents/ BaseAgent eingebettet |
| ADR-008 | Revenue-Gate-Bedingung für diesen ADR |

---

## Trigger für Implementierungsstart

- Erster Gumroad-Revenue (CNA CLI oder MethodenOS) bestätigt
- ADR-009 Status wechselt von PROPOSED → ACCEPTED
- Erster Commit in cognitum_core/ als Startsignal
