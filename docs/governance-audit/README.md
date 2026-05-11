# Governance audit reports

This directory stores reviewable audit reports generated from the COGNITUM governance Single Source of Truth and validated with AgentsProtocol.

## Generate a report

From the repository root:

```bash
python cognitum/scripts/export_governance_claims.py
```

The command reads:

- `cognitum/governance/masterplan.yaml`

It exports claims for:

- constitution articles,
- architecture decisions,
- modules,
- ISO 23894 risks,
- privacy invariants.

Then it validates those claims with AgentsProtocol:

- `compute_s_con`
- `compute_psi`
- `check_acceptance`

For a CI-style quality gate:

```bash
python cognitum/scripts/export_governance_claims.py --fail-on-reject
```

## Outputs

- `latest.json` is the tracked current audit report.
- Minute-versioned reports are written as `YYYY-MM-DD_HH-MM.json`.

## Integrity fields

Each report contains:

- `report_version`
- `source_sha256` for `cognitum/governance/masterplan.yaml`
- `original_claim_sha256` for each exported governance claim
- `integrity.report_payload_sha256`
- optional HMAC-SHA256 signature metadata

To sign a report without storing a secret in Git:

```bash
export GOVERNANCE_AUDIT_HMAC_KEY="replace-with-secret"
python cognitum/scripts/export_governance_claims.py
```

If the environment variable is absent, the report is explicitly marked as `unsigned`.

## Validators

Built-in validators are deterministic and CI-safe:

| Name | Purpose |
| --- | --- |
| `baseline` | Self-consistency quality gate for reliable CI behavior. |
| `kind-context` | Scores each claim against claims of the same governance kind. |
| `full-context` | Scores each claim against the full exported governance corpus. |

Run multiple built-ins:

```bash
python cognitum/scripts/export_governance_claims.py --validators baseline,kind-context
```

External validators can be attached with `--validator-results path/to/results.json`.
Expected shape:

```json
{
  "validators": [
    {
      "name": "independent-validator-a",
      "description": "Optional human readable description",
      "scores": {
        "<claim-id>": 0.95
      }
    }
  ]
}
```

Every external validator must provide a score in `[0.0, 1.0]` for every exported claim. `Psi` is computed from the validator error vectors relative to the first validator in the report.

## Interpretation

The default integration is a deterministic baseline: each governance claim is checked for semantic self-consistency and validator independence through AgentsProtocol primitives. The next maturity step is to add independent validator result files produced by separate validator processes or services.
