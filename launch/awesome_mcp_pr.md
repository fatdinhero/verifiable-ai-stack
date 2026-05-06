# PR for awesome-mcp-servers

**PR Title:** Add VeriEthicCore — EU AI Act compliance MCP server

**PR Body:**

## New server: VeriEthicCore

Adds **VeriEthicCore** to the compliance/legal category.

### What it does

Local MCP server for EU AI Act (2024/1689) compliance checking. Five tools cover the full regulatory pipeline:

- **check_prohibited_practices** — Art. 5 prohibited AI practice detection
- **classify_risk_level** — Art. 6 / Annex III risk classification (prohibited / high / limited / minimal)
- **check_transparency_obligations** — Art. 50 obligations for chatbots, emotion recognition, synthetic content
- **check_hleg_trustworthy_ai** — HLEG Ethics Guidelines 28-point Trustworthy AI checklist
- **generate_full_compliance_report** — consolidated report with SHA-256 audit fingerprint

### Why it belongs here

- **Local-first** — stdio transport, zero network calls, zero telemetry
- **Audit-ready** — SHA-256 fingerprinted reports for regulators
- **Actively maintained** — part of the COGNITUM governance ecosystem
- **EU AI Act enforcement begins August 2026** — high developer urgency now

### Installation

```bash
pip install fastmcp pydantic
python -m veriethiccore.server
```

### Checklist (awesome-mcp-servers contribution guidelines)

- [x] Server runs locally without cloud dependencies
- [x] Clear description of tools and use cases
- [x] Open source / inspectable code
- [x] Author contact provided

### Suggested entry

```markdown
- [VeriEthicCore](https://gitlab.com/fatdinhero/cognitum) — EU AI Act (2024/1689) compliance:
  risk classification, prohibited practice detection, HLEG 28-point Trustworthy AI scoring,
  SHA-256 audited reports. Local-first, stdio transport.
```
