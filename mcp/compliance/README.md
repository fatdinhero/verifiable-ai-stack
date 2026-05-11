# MCP compliance facade

This folder will host adapters that expose compliance modules through the future VeriMCP server.

## Adapter rule

Adapters should:

- call compliance modules through their public functions or server entry points,
- preserve the original rule IDs and evidence,
- normalize output shape only at the boundary,
- avoid embedding domain-specific policy logic in MCP routing code.

## Domains

- EU AI Act: `compliance/eu-ai-act/`
- Halal policy: `compliance/halal/`
- zkHalal proofs: `compliance/zkhalal-mcp/`
- COS backend alignment: `civilization-operating-system/`
