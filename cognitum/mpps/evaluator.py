#!/usr/bin/env python3
"""
evaluator.py v2 – Mit LLM-as-Judge + Adversarial Testing
"""

import json
import ollama
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class EvaluationResult:
    adr_id: str
    spalten_completeness: float
    vdi2225_accuracy: float
    tool_use_accuracy: float
    process_score: float
    llm_judge_score: float
    overall_score: float
    details: Dict[str, Any]
    timestamp: str

class MPPS_Evaluator:
    def __init__(self, model_name: str = "mpps-qwen-7b-v1", judge_model: str = "qwen2.5:7b-instruct-q4_K_M"):
        self.model_name = model_name
        self.judge_model = judge_model
        self.results: List[EvaluationResult] = []

    def check_spalten_completeness(self, adr: Dict) -> float:
        trace = adr.get("spalten_trace", {})
        phases = ["S", "P", "A", "L", "T", "E", "N"]
        score = sum(1 for phase in phases if phase in trace and len(str(trace[phase])) > 15)
        return round(score / len(phases), 3)

    def check_vdi2225_accuracy(self, adr: Dict, human_score: Optional[float] = None) -> float:
        model_score = adr.get("final_artifacts", {}).get("score", 0.0)
        if human_score is not None:
            return round(1.0 - abs(model_score - human_score), 3)
        return 0.85 if 0.65 <= model_score <= 0.92 else 0.5

    def check_tool_use(self, adr: Dict) -> float:
        tool_calls = adr.get("tool_calls", [])
        if not tool_calls:
            return 0.25
        valid = ["registry.calculate_rpn", "registry.get_action_priority", "vdi2225_evaluate"]
        return min(sum(0.3 for call in tool_calls if call.get("tool") in valid), 1.0)

    def process_oriented_score(self, adr: Dict) -> float:
        score = 0.0
        trace = adr.get("spalten_trace", {})
        if len(trace.get("A", {}).get("alternatives", [])) >= 3: score += 0.25
        if trace.get("L", {}).get("vdi2225_score"): score += 0.25
        if adr.get("reflection") and len(adr.get("reflection", "")) > 40: score += 0.25
        if trace.get("N", {}).get("lessons_learned"): score += 0.25
        return round(score, 3)

    def llm_as_judge(self, adr: Dict) -> float:
        prompt = f"""Du bist ein strenger VDI-2225 und SPALTEN-Auditor.
Bewerte das folgende ADR von 0.0 bis 1.0. Gib nur die Zahl zurück.

ADR: {json.dumps(adr, indent=2, ensure_ascii=False)[:2200]}"""
        try:
            response = ollama.chat(model=self.judge_model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.1})
            return round(min(max(float(response['message']['content'].strip()), 0.0), 1.0), 3)
        except:
            return self.process_oriented_score(adr)

    def generate_adversarial_cases(self, base_problems: List[str]) -> List[Dict]:
        return [{"id": f"adv_{p[:15]}", "feature_description": p, "spalten_trace": {"L": {"vdi2225_score": 0.45}}, "final_artifacts": {"score": 0.45}} for p in base_problems]

    def evaluate_adr(self, adr: Dict, human_score: Optional[float] = None) -> EvaluationResult:
        spalten = self.check_spalten_completeness(adr)
        vdi = self.check_vdi2225_accuracy(adr, human_score)
        tool = self.check_tool_use(adr)
        process = self.process_oriented_score(adr)
        llm = self.llm_as_judge(adr)
        overall = round(spalten*0.18 + vdi*0.18 + tool*0.14 + process*0.25 + llm*0.25, 3)
        
        result = EvaluationResult(adr_id=adr.get("id", "unknown"), spalten_completeness=spalten, vdi2225_accuracy=vdi,
                                  tool_use_accuracy=tool, process_score=process, llm_judge_score=llm, overall_score=overall,
                                  details={"feature": adr.get("feature_description", "")}, timestamp=datetime.utcnow().isoformat())
        self.results.append(result)
        return result

    def evaluate_batch(self, adrs: List[Dict]) -> Dict[str, Any]:
        for adr in adrs:
            self.evaluate_adr(adr)
        avg = sum(r.overall_score for r in self.results) / len(self.results) if self.results else 0
        return {
            "model": self.model_name,
            "timestamp": datetime.utcnow().isoformat(),
            "total": len(self.results),
            "average_overall": round(avg, 3),
            "pass_rate_0.80": len([r for r in self.results if r.overall_score >= 0.80]),
            "results": [asdict(r) for r in self.results]
        }

    def save_report(self, report: Dict, filename: str = None):
        if filename is None:
            filename = f"evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        Path("data/evaluation").mkdir(parents=True, exist_ok=True)
        with open(f"data/evaluation/{filename}", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ Report gespeichert: data/evaluation/{filename}")
