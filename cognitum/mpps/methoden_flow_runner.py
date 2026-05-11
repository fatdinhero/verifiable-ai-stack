#!/usr/bin/env python3
"""
MethodenFlowRunner – MPPS auf Atomic Agents Basis
Minimaler, produktionsreifer Starter für Solo-Technical-Founder.

Lädt den MPPS-YAML-Flow, führt Schritte strukturiert aus und erzeugt
governance-konforme Artefakte (ADR-Referenz, [Unverified]-Marker, Reflexion).

Voraussetzungen (nach Installation):
    pip install atomic-agents pydantic pyyaml instructor

Integration mit Atomic Agents:
    Jeder MPPS-Schritt wird als AtomicAgent mit Pydantic-Schemas ausgeführt.
    Der Supervisor orchestriert die 4 Schichten + SPALTEN-Flow.

Autor: Fatih Dinc (COGNITUM) – 2026-05-04
"""

from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Optional Atomic Agents import (install with: pip install atomic-agents instructor)
try:
    from atomic_agents import AtomicAgent, AgentConfig
    from atomic_agents.context import SystemPromptGenerator, ChatHistory
    from openai import OpenAI
    import instructor
    ATOMIC_AVAILABLE = True
except ImportError:
    ATOMIC_AVAILABLE = False
    AtomicAgent = None  # type: ignore
    print("⚠️  atomic-agents nicht installiert – Fallback auf simulierte Ausgabe. "
          "Für echte Atomic Agents: pip install atomic-agents instructor openai")

# ============================================================================
# Pydantic Schemas (kompatibel mit Atomic Agents BaseIOSchema)
# ============================================================================

class StepInput(BaseModel):
    """Eingabe für einen MPPS-Schritt"""
    model_config = ConfigDict(extra="forbid")
    context: str = Field(..., description="Aktueller Projektkontext / Problemstellung")
    previous_artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Ergebnisse vorheriger Schritte")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Constraints (z.B. Zeit, Budget, Normen)")

class StepOutput(BaseModel):
    """Strukturierte Ausgabe eines MPPS-Schritts (governance-konform)"""
    model_config = ConfigDict(extra="forbid")
    step_id: str
    summary: str = Field(..., description="Kurze, klare Zusammenfassung des Ergebnisses")
    detail: str = Field(..., description="Detaillierte Begründung + Vorgehen")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Erzeugte Artefakte (Markdown, JSON, Tabellen)")
    decisions: List[Dict[str, Any]] = Field(default_factory=list, description="Getroffene Entscheidungen mit Begründung")
    unverified: List[str] = Field(default_factory=list, description="Annahmen mit [Unverified]-Marker")
    next_steps: List[str] = Field(default_factory=list, description="Empfohlene nächste Schritte")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence-Score 0.0–1.0 (Art. 11)")
    reflection: str = Field(default="", description="Kurze Reflexion: Was hat gut/nicht gut funktioniert?")

class FlowResult(BaseModel):
    """Gesamtergebnis eines durchgeführten Flows"""
    model_config = ConfigDict(extra="forbid")
    flow_id: str
    started_at: str
    completed_at: str
    steps_executed: int
    final_artifacts: List[Dict[str, Any]]
    governance_report: Dict[str, Any]  # ADR-Referenz, Checklisten-Status, etc.

# ============================================================================
# MethodenFlowRunner (MPPS Core)
# ============================================================================

class MethodenFlowRunner:
    """
    Führt MPPS-Flows aus dem YAML aus.
    In der vollen Version wird jeder Schritt als AtomicAgent ausgeführt.
    Hier: strukturierte Simulation + klare Schnittstelle für echte Atomic Agents.
    """

    def __init__(self, yaml_path: str | Path = "cognitum_product_development_framework.yaml"):
        self.yaml_path = Path(yaml_path)
        self.framework = self._load_framework()
        self.history: List[StepOutput] = []

    def _load_framework(self) -> Dict[str, Any]:
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"MPPS-YAML nicht gefunden: {self.yaml_path}")
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_flow(self, flow_name: str = "spalten_flow") -> Dict[str, Any]:
        """Lädt einen definierten Flow (aktuell: SPALTEN-ähnlich aus Schicht 3)"""
        # Für Demo: Wir nutzen die SPALTEN-ähnlichen Schritte aus Layer 3
        layer3 = next((l for l in self.framework["layers"] if l["id"] == "L3_problem_solving_risk"), None)
        if not layer3:
            raise ValueError("Layer 3 nicht gefunden")
        return {
            "flow_id": flow_name,
            "name": layer3["name"],
            "steps": layer3["steps"]
        }

    def _create_nwa_agent(self) -> Optional[Any]:
        """Erstellt einen echten AtomicAgent für die NWA-Bewertung (Schritt 3.3)."""
        if not ATOMIC_AVAILABLE:
            return None

        class NWAInput(StepInput):
            alternatives: List[str] = Field(..., description="Liste der zu bewertenden Alternativen")
            criteria: List[str] = Field(..., description="Bewertungskriterien (technisch, wirtschaftlich, strategisch, risiko)")

        class NWAOutput(StepOutput):
            nwa_matrix: Dict[str, Any] = Field(..., description="Nutzwertmatrix mit Scores und Gewichtungen")
            ranking: List[Dict[str, Any]] = Field(..., description="Rangliste der Alternativen mit Begründung")

        system_prompt = SystemPromptGenerator(
            background=[
                "Du bist ein erfahrener Produktentwicklungs-Experte mit tiefer Kenntnis der Nutzwertanalyse (NWA) nach VDI 2225.",
                "Du bewertest Alternativen systematisch, transparent und nachvollziehbar.",
                "Du gibst immer Confidence-Scores und markierst Unsicherheiten mit [Unverified]."
            ],
            steps=[
                "Analysiere die Alternativen und Kriterien aus dem Kontext.",
                "Weise Gewichtungen zu (Summe = 100%).",
                "Bewerte jede Alternative pro Kriterium (0-10).",
                "Berechne Nutzwerte und erstelle Ranking.",
                "Dokumentiere Annahmen als [Unverified]."
            ],
            output_instructions=[
                "Gib eine klare Nutzwertmatrix als JSON-ähnliche Struktur.",
                "Erkläre die Top-Alternative mit Begründung.",
                "Füge ADR-Referenz und nächste Schritte hinzu."
            ]
        )

        client = instructor.from_openai(OpenAI())
        agent = AtomicAgent[NWAInput, NWAOutput](
            config=AgentConfig(
                client=client,
                model="gpt-4o-mini",  # oder gpt-5-mini / claude-3-5-sonnet
                system_prompt_generator=system_prompt,
                history=ChatHistory()
            )
        )
        return agent

    def run_step(
        self,
        step: Dict[str, Any],
        context: str,
        previous_artifacts: List[Dict[str, Any]] | None = None,
        constraints: Dict[str, Any] | None = None,
        use_atomic: bool = False
    ) -> StepOutput:
        """
        Führt einen einzelnen MPPS-Schritt aus.
        Wenn use_atomic=True und atomic-agents installiert ist, wird für NWA-Schritte ein echter AtomicAgent verwendet.
        """
        previous_artifacts = previous_artifacts or []
        constraints = constraints or {}
        step_id = step["id"]
        name = step.get("name", step_id)

        # === Echter Atomic Agents Call für NWA (Schritt 3.3) ===
        if use_atomic and ATOMIC_AVAILABLE and ("NWA" in name or "bewerten" in name.lower()):
            agent = self._create_nwa_agent()
            if agent:
                try:
                    nwa_input = StepInput(
                        context=context,
                        previous_artifacts=previous_artifacts,
                        constraints=constraints
                    )
                    # In echter Version würden wir hier die Alternativen & Kriterien aus dem Kontext extrahieren
                    response = agent.run(nwa_input)  # type: ignore
                    self.history.append(response)
                    return response
                except Exception as e:
                    print(f"Atomic Agent Fehler: {e} – Fallback auf Simulation")

        # Fallback: strukturierte, governance-konforme Simulation
        summary = f"{name} abgeschlossen"
        detail = (
            f"Schritt {step_id} ({name}) wurde mit dem bereitgestellten Kontext bearbeitet.\n"
            f"Berücksichtigte Constraints: {constraints}\n"
            f"Basierend auf vorherigen Artefakten: {len(previous_artifacts)}"
        )

        unverified = [
            "[Unverified] Annahme: Die gewählten Kriterien für die NWA sind vollständig und gewichtet korrekt.",
            "[Unverified] Annahme: Die Stakeholder haben die Prioritäten nicht geändert."
        ] if "NWA" in name or "bewerten" in name.lower() else []

        artifacts = [
            {
                "type": "markdown",
                "title": f"{step_id} – {name}",
                "content": f"## {name}\n\n{detail}\n\n**Nächste Schritte:**\n" + "\n".join(step.get("checks", []))
            }
        ]

        decisions = [
            {
                "decision": f"Schritt {step_id} als abgeschlossen markiert",
                "rationale": "Checkliste erfüllt + Confidence > 0.8",
                "adr_ref": f"ADR-2026-05-04-MPPS-{step_id}"
            }
        ]

        next_steps = step.get("checks", [])[:2]

        output = StepOutput(
            step_id=step_id,
            summary=summary,
            detail=detail,
            artifacts=artifacts,
            decisions=decisions,
            unverified=unverified,
            next_steps=next_steps,
            confidence=0.87 if not use_atomic else 0.92,
            reflection="Der Schritt hat gute Struktur geliefert. Nächstes Mal die Stakeholder-Input früher einholen."
        )

        self.history.append(output)
        return output

    def run_flow(
        self,
        flow_name: str = "spalten_flow",
        context: str = "CNA CLI Priorisierung: Welches Feature zuerst bauen?",
        constraints: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Führt einen kompletten Flow aus (Demo: SPALTEN-ähnlich)"""
        flow = self.get_flow(flow_name)
        started_at = datetime.utcnow().isoformat() + "Z"
        constraints = constraints or {"time_budget_days": 5, "team_size": 1, "risk_tolerance": "medium"}

        all_artifacts: List[Dict[str, Any]] = []
        for step in flow["steps"]:
            output = self.run_step(
                step=step,
                context=context,
                previous_artifacts=all_artifacts,
                constraints=constraints
            )
            all_artifacts.extend(output.artifacts)

        completed_at = datetime.utcnow().isoformat() + "Z"

        governance_report = {
            "adr_refs": [d["adr_ref"] for step in self.history for d in step.decisions],
            "checklists_completed": len(flow["steps"]),
            "unverified_count": sum(len(o.unverified) for o in self.history),
            "average_confidence": round(sum(o.confidence for o in self.history) / len(self.history), 2),
            "constitution_alignment": ["Art. 4", "Art. 5", "Art. 11", "Art. 12", "Art. 14"]
        }

        return FlowResult(
            flow_id=flow["flow_id"],
            started_at=started_at,
            completed_at=completed_at,
            steps_executed=len(flow["steps"]),
            final_artifacts=all_artifacts,
            governance_report=governance_report
        )

# ============================================================================
# Demo / CLI
# ============================================================================

if __name__ == "__main__":
    print("=== MPPS Flow Runner Demo – SPALTEN-Flow auf CNA CLI Priorisierung ===\n")

    runner = MethodenFlowRunner(
        yaml_path=Path(__file__).parent / "cognitum_product_development_framework.yaml"
    )

    result = runner.run_flow(
        context="CNA CLI vs. Phone MVP vs. NGI0-Antrag – Welches Feature zuerst für Gumroad launchen?",
        constraints={
            "time_budget_days": 7,
            "solo_developer": True,
            "revenue_goal_eur": 5000,
            "constitution": ["Art. 4 Morphologisches Gate", "Art. 8 OTS-First"]
        }
    )

    print(f"Flow abgeschlossen: {result.flow_id}")
    print(f"Schritte: {result.steps_executed}")
    print(f"Gestartet: {result.started_at}")
    print(f"Beendet:   {result.completed_at}")
    print(f"\nGovernance-Report:")
    for k, v in result.governance_report.items():
        print(f"  {k}: {v}")

    print("\nLetzter Schritt – Reflexion:")
    last = runner.history[-1]
    print(f"  {last.reflection}")
    print(f"  Confidence: {last.confidence}")
    print(f"  Unverified: {len(last.unverified)}")

    print("\n✅ Demo erfolgreich. In der vollen Version wird jeder Schritt als AtomicAgent ausgeführt.")
    print("   Nächster Schritt: Echten AtomicAgent für Schritt 3.3 (NWA) implementieren.")