# EU AI Act compliance

This folder hosts the VeriEthicCore EU AI Act MCP module moved out of the former COGNITUM root into the dedicated compliance layer.

## Package

```text
compliance/eu-ai-act/
└── veriethiccore/
    ├── server.py
    ├── mcp_server.py
    ├── act_checker.py
    └── eu_ai_act_rules.py
```

Run from this directory so the `veriethiccore` Python package resolves correctly:

```bash
cd compliance/eu-ai-act
python -m veriethiccore.server
```

## Boundary

This module evaluates EU AI Act compliance signals. COGNITUM remains the governance Single Source of Truth that decides how findings affect product releases, ADRs, and risk treatment.
