#!/usr/bin/env python3
"""
cli_runner.py
Terminal-Interface für MPPS / COGNITUM Engineering Agent
"""

import argparse
from mpps_orchestrator import MPPSOrchestrator

def main():
    parser = argparse.ArgumentParser(description="MPPS CLI Runner")
    parser.add_argument("--problem", type=str, required=True, help="Problemstellung")
    parser.add_argument("--domain", type=str, default="cna_cli", help="Domain (cna_cli, opex_service, ...)")
    parser.add_argument("--urgency", type=str, default="high", choices=["low", "medium", "high", "critical"])
    args = parser.parse_args()

    orch = MPPSOrchestrator()
    print(f"🚀 Starte SPALTEN für: {args.problem}")
    result = orch.run_spalten(args.problem, args.domain, args.urgency)
    print("✅ Fertig. Ergebnis:")
    print(result)

if __name__ == "__main__":
    main()