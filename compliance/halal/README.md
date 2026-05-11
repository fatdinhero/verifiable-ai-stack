# Halal compliance policy

This folder is the shared policy bridge between:

- `civilization-operating-system/` for Sharia-compliant backend logic,
- `compliance/zkhalal-mcp/` for zero-knowledge Sharia compliance tooling,
- `cognitum/` for governance and release decisions.

## Current role

The folder intentionally starts as documentation and policy glue. Runtime code should only be added once there is a stable contract between COS, zkHalal MCP, and COGNITUM governance.

## Policy boundary

Automated checks may classify obvious cases and produce evidence, but final high-impact religious or financial judgments should support human or qualified review workflows.

## Finding shape

```json
{
  "domain": "halal",
  "status": "halal|haram|mashbooh|needs_review",
  "basis": ["riba", "gharar", "maysir"],
  "confidence": 0.0,
  "human_review_required": true
}
```
