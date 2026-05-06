# Show HN: VeriEthicCore — EU AI Act compliance as an MCP server

**Show HN post draft**

---

**Title:** Show HN: VeriEthicCore – EU AI Act compliance checker as a local MCP server

**Body:**

Hey HN,

I built VeriEthicCore — an MCP (Model Context Protocol) server that runs EU AI Act (2024/1689) compliance checks directly in Claude Code, Cursor, or any MCP-compatible client.

**Why:** The EU AI Act is enforceable from August 2026. Most compliance tooling is either SaaS (sends your architecture docs to a cloud) or a static checklist PDF. I wanted something that:
1. Runs 100% locally — no data leaves your machine
2. Integrates into the AI-assisted dev workflow (MCP)
3. Produces reproducible audit trails (SHA-256 fingerprinted reports)

**What it does (5 tools):**
- `check_prohibited_practices` — detects Art. 5 prohibited AI patterns in a system description
- `classify_risk_level` — classifies as prohibited / high / limited / minimal (Art. 6 / Annex III)
- `check_transparency_obligations` — Art. 50 checks for chatbots and emotion AI
- `check_hleg_trustworthy_ai` — 28-point HLEG Trustworthy AI checklist with a 0–1 score
- `generate_full_compliance_report` — complete report with SHA-256 fingerprint for audit trails

**Stack:** Python, FastMCP (stdio transport), zero external API calls.

**Install:**
```bash
pip install fastmcp pydantic
python -m veriethiccore.server
```

Source: https://gitlab.com/fatdinhero/cognitum

Happy to answer questions about the EU AI Act articles or the MCP integration pattern.
