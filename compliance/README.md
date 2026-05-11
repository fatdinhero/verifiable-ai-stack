# Compliance layer

The compliance layer keeps regulatory and ethical checks modular. It does not own product truth; it produces structured findings that COGNITUM governance can accept, reject, or escalate.

## Structure

```text
compliance/
├── eu-ai-act/       # EU AI Act MCP server and rule checks
├── halal/           # Shared halal policy and integration notes
└── zkhalal-mcp/     # Zero-knowledge Sharia compliance MCP module
```

## Responsibilities

- **EU AI Act:** risk classification, article mapping, and compliance evidence.
- **Halal:** shared policy vocabulary, COS alignment, and human-review boundary.
- **zkHalal MCP:** privacy-preserving Sharia compliance checks and proof artifacts.

## Integration rule

Compliance outputs should be explicit JSON-like findings:

```json
{
  "domain": "eu-ai-act",
  "status": "pass|warn|fail|needs_review",
  "rule_id": "string",
  "summary": "string",
  "evidence": []
}
```

The future VeriMCP facade in `mcp/compliance/` should aggregate these findings without hiding their source domain.
