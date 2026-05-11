# VeriMCP

VeriMCP is the integration layer for `verifiable-ai-stack`: a lightweight FastAPI facade that composes COGNITUM governance, AgentsProtocol semantic validation, and baseline compliance checks.

## Architecture

```text
VeriMCP FastAPI server
  -> cognitum/scripts/export_governance_claims.py
     -> governance claims
     -> AgentsProtocol S_con / Psi / check_acceptance
     -> audit report v2.4
  -> compliance/eu-ai-act/veriethiccore
     -> EU AI Act + HLEG baseline report
  -> halal baseline adapter
     -> Riba / Gharar / Maysir screening
```

VeriMCP composes lower layers. It does not duplicate the governance Single Source of Truth or protocol algorithms.

## Quick start

From the repository root:

```bash
python -m pip install fastapi uvicorn pydantic pyyaml numpy scipy
uvicorn app:app --app-dir mcp/server --host 127.0.0.1 --port 8088
```

Then call:

```bash
curl http://127.0.0.1:8088/health
```

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Server health and version. |
| `POST /governance/claims` | Export governance claims from COGNITUM. |
| `POST /governance/audit` | Validate governance claims with AgentsProtocol and optionally write an audit report. |
| `POST /compliance/check` | Run baseline EU AI Act and Halal checks. |

Example governance audit:

```bash
curl -X POST http://127.0.0.1:8088/governance/audit \
  -H 'content-type: application/json' \
  -d '{"limit": 5, "validators": ["baseline"], "include_claims": false}'
```

Example compliance check:

```bash
curl -X POST http://127.0.0.1:8088/compliance/check \
  -H 'content-type: application/json' \
  -d '{
    "system_name": "DaySensOS",
    "system_description": "Privacy-first wearable AI coach",
    "domain": "wearable health",
    "processes_biometrics": false,
    "halal": {"protocol_name": "spot", "transaction_type": "purchase"}
  }'
```

## Structure

```text
mcp/
├── server/           # FastAPI VeriMCP server
├── compliance/       # compliance facade notes and future adapters
├── semantic-layer/   # compatibility wrappers around COGNITUM governance export
└── tests/            # VeriMCP API tests
```

## Design rules

- COGNITUM owns `governance/masterplan.yaml`.
- AgentsProtocol owns semantic validation primitives.
- Compliance modules own domain-specific rule logic.
- VeriMCP only composes and exposes stable API boundaries.
- No user data is required for the governance audit path.
