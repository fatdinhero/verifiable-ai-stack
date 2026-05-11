# VeriMCP FastAPI server

This folder contains the first runnable VeriMCP server.

## Run

```bash
uvicorn app:app --app-dir mcp/server --host 127.0.0.1 --port 8088
```

## API surface

- `GET /health`
- `POST /governance/claims`
- `POST /governance/audit`
- `POST /compliance/check`

## Implementation notes

- Governance and semantic validation are delegated to `cognitum/scripts/export_governance_claims.py`.
- EU AI Act checks use `compliance/eu-ai-act/veriethiccore/eu_ai_act_rules.py`.
- Halal screening is a small baseline adapter aligned with zkHalal/COS categories and designed to be replaced by a direct `zkhalal-mcp` adapter later.
- Errors at API boundaries are converted to HTTP responses and logged through the `verimcp` logger.
