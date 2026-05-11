# PulseMCP Submission Email

**To:** mike@pulsemcp.com  
**Subject:** New MCP server submission: VeriEthicCore — EU AI Act Compliance

---

Hi Mike,

I'd like to submit **VeriEthicCore** for listing on PulseMCP.

**What it is:** A local MCP server that provides EU AI Act (2024/1689) compliance tools — risk classification, prohibited practice detection, transparency obligation checks, and full HLEG 28-point Trustworthy AI scoring.

**Why it's relevant for the MCP ecosystem:**
- EU AI Act enforcement starts August 2026; developers building AI products need this now
- 100% local (stdio transport) — no cloud, no telemetry, no data sent anywhere
- SHA-256 fingerprinted reports for reproducible audit trails
- Works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client

**5 tools:**
1. `check_prohibited_practices` — Art. 5 prohibited AI detection
2. `classify_risk_level` — Art. 6 / Annex III risk classification
3. `check_transparency_obligations` — Art. 50 transparency requirements
4. `check_hleg_trustworthy_ai` — 28-point HLEG checklist
5. `generate_full_compliance_report` — full audit with SHA-256 hash

**Install:** `pip install fastmcp pydantic && python -m veriethiccore.server`

**Source:** https://gitlab.com/fatdinhero/cognitum  
**Author:** Fatih Dinc (fatdinhero@gmail.com)

Happy to provide any additional details or a demo.

Best,  
Fatih Dinc
