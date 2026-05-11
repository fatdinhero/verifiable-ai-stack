#!/usr/bin/env python3
"""
adr_generator.py
Erzeugt automatisch hochwertige synthetische ADRs
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from cognitum_engineering_agent import CognitumEngineeringAgent

class ADRGenerator:
    def __init__(self):
        self.agent = CognitumEngineeringAgent()
        self.output_dir = Path("data/synthetic_adrs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_adr(self, problem: str, domain: str = "cna_cli") -> Dict:
        print(f"🧠 Generiere ADR für: {problem}")
        result = self.agent.run(problem=problem, domain=domain)
        
        if not result or not result.get("selected_solution"):
            return None

        adr = {
            "id": f"synthetic_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "domain": domain,
            "feature_description": problem,
            "spalten_trace": {
                "S": result.get("situation", {}),
                "P": result.get("problem_definition", {}),
                "A": {"alternatives": result.get("alternatives", [])},
                "L": {"selected_solution": result.get("selected_solution", {})},
                "T": result.get("risk_assessment", {}),
                "E": result.get("implementation_plan", {}),
                "N": {"lessons_learned": result.get("lessons_learned", [])}
            },
            "reasoning_chain": result.get("reasoning_chain", ""),
            "tool_calls": result.get("tool_calls", []),
            "reflection": result.get("reflection", ""),
            "final_artifacts": {
                "adr_markdown": result.get("adr_content", ""),
                "score": result.get("selected_solution", {}).get("score", 0.0)
            },
            "quality_metrics": {"overall_score": result.get("confidence", 0.0)},
            "source": "mpps_v0.2_synthetic",
            "license": "MIT"
        }
        
        filename = f"{adr['id']}.json"
        with open(self.output_dir / filename, "w", encoding="utf-8") as f:
            json.dump(adr, f, indent=2, ensure_ascii=False)
        
        print(f"✅ ADR gespeichert: {filename}")
        return adr

    def generate_batch(self, problems: List[str], domain: str = "cna_cli") -> List[Dict]:
        results = []
        for problem in problems:
            adr = self.generate_adr(problem, domain)
            if adr:
                results.append(adr)
        print(f"\n✅ {len(results)} ADRs erfolgreich generiert")
        return results

if __name__ == "__main__":
    generator = ADRGenerator()
    test_problems = [
        "CNA CLI Performance Degradation bei >10 Concurrent Users",
        "DaySensOS Sensor-Datenverarbeitung skalieren"
    ]
    generator.generate_batch(test_problems)
