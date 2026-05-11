# VeriEthicCore — EU AI Act Compliance MCP Server

## Smithery.ai Listing

**Name:** VeriEthicCore  
**Category:** Compliance / AI Governance  
**Transport:** stdio  
**Runtime:** Python 3.9+

---

### What it does

VeriEthicCore gives your Claude Code workflow instant EU AI Act (2024/1689) compliance checking without leaving your IDE. Five tools cover the full compliance pipeline:

| Tool | Regulation |
|------|-----------|
| `check_prohibited_practices` | Art. 5 — prohibited AI |
| `classify_risk_level` | Art. 6 / Annex III — risk tiers |
| `check_transparency_obligations` | Art. 50 — chatbot & emotion AI |
| `check_hleg_trustworthy_ai` | HLEG 28-point checklist |
| `generate_full_compliance_report` | Full audit + SHA-256 fingerprint |

### Why it's different

- **Local-first** — zero network calls, zero telemetry
- **Audit-ready** — every full report includes a SHA-256 fingerprint for reproducible audit trails
- **28-point HLEG** — covers all three HLEG pillars (lawful, ethical, robust)
- **5-minute setup** — one `pip install`, one config line in Claude Desktop

### Installation

```bash
pip install fastmcp pydantic
python -m veriethiccore.server
```

Claude Desktop `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "veriethiccore": {
      "command": "python",
      "args": ["-m", "veriethiccore.server"]
    }
  }
}
```

### Use cases

- Classify an AI system before deployment
- Generate a conformity assessment for regulators
- Spot prohibited practices in architecture documents
- Score AI projects against the HLEG Trustworthy AI framework
