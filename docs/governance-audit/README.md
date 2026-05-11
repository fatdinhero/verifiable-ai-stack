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

- `report_schema` (`verifiable-ai-stack/governance-audit/v2.2`)
- `report_version`
- structured `metadata` with tool, runtime, Git commit, and GitHub Actions context when available
- `source_sha256` for `cognitum/governance/masterplan.yaml`
- `original_claim_sha256` for each exported governance claim
- `quality_gate` with thresholds, observed values, and pass/fail status
- `integrity.report_payload_sha256`
- optional HMAC-SHA256 signature metadata

To sign a report without storing a secret in Git:

```bash
export GOVERNANCE_AUDIT_HMAC_KEY="replace-with-secret"
python cognitum/scripts/export_governance_claims.py
```

If the environment variable is absent, the report is explicitly marked as `unsigned`.

### Key management

- Store `GOVERNANCE_AUDIT_HMAC_KEY` only in CI/repository secrets or an approved secret manager.
- Rotate the key if it is exposed in logs, reports, commits, or local terminals.
- Do not use personal passwords as HMAC keys.
- For stricter environments, replace HMAC with an external signing service or Ed25519 signer and keep the private key outside the repository.

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

External validators can also be fetched from an HTTP(S) API:

```bash
python cognitum/scripts/export_governance_claims.py \
  --validator-api https://validator-a.example.com/audit,https://validator-b.example.com/audit \
  --validator-api-timeout 15 \
  --validator-api-retries 2 \
  --fail-on-reject
```

The API must return the same JSON shape as `--validator-results`. Network and schema errors fail closed before validation. API validators are executed in parallel with built-in validators and local result-file validators. Retries use bounded exponential backoff.

## Adding a new validator

Use one of two paths:

1. **Built-in deterministic validator:** add a `ValidatorProfile` entry in `BUILT_IN_VALIDATORS` inside `cognitum/scripts/export_governance_claims.py`. Use this for CI-safe, local, reproducible validation strategies.
2. **Independent external validator:** run a separate process or service that receives exported claim IDs/statements and returns the `validators[].scores` JSON structure shown above. Attach it with `--validator-results` or `--validator-api`.

For regulated environments, prefer independent external validators operated in separate trust domains. Keep validator output immutable, signed, and archived with the audit report.

Recommended validator metadata:

- `name`: stable validator identifier,
- `version`: validator implementation or ruleset version,
- `description`: short purpose and trust-domain note,
- `scores`: complete claim-id to score mapping.

## CI quality gate

`.github/workflows/governance-audit.yml` runs on push, pull requests, and manual dispatch. It:

1. installs audit dependencies,
2. runs `cognitum/scripts/export_governance_claims.py --fail-on-reject`,
3. validates the generated report shape,
4. writes a GitHub Step Summary with quality-gate details,
5. uploads the audit report as a workflow artifact with run-specific naming and 90-day retention,
6. fails the job when `check_acceptance` rejects the report.

The workflow includes a commented Slack/Teams notification template for regulated deployments. Keep notification payloads free of secrets and private user data.

## Interpretation

The default integration is a deterministic baseline: each governance claim is checked for semantic self-consistency and validator independence through AgentsProtocol primitives. The next maturity step is to add independent validator result files produced by separate validator processes or services.
