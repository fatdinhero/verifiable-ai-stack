# VeriMCP integration layer

`mcp/` is the composition layer for governance, semantic validation, and compliance tools. It should expose stable interfaces without copying business logic from imported components.

## Structure

```text
mcp/
├── server/           # future VeriMCP server and registry metadata
├── compliance/       # compliance facade notes and adapters
└── semantic-layer/   # governance-claim export and AgentsProtocol bridge
```

## Current bridge

The first bridge exports COGNITUM governance entries as deterministic claims and validates them with AgentsProtocol:

```bash
python mcp/semantic-layer/governance_claims.py --limit 5
python mcp/semantic-layer/validate_governance_claims.py --limit 5
```

## Design rule

MCP code composes lower layers. If logic belongs to COGNITUM, AgentsProtocol, PoISV, or a compliance module, keep it there and call it through a documented interface.
