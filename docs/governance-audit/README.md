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

## Outputs

- `latest.json` is the tracked current audit report.
- Timestamped `governance-audit-*.json` snapshots are generated locally and ignored by Git to avoid noisy commits.

## Interpretation

The current integration is a deterministic baseline: each governance claim is checked for semantic self-consistency and validator independence through AgentsProtocol primitives. The next maturity step is to replace the deterministic baseline corpus with a signed or IPFS-addressed governance evidence corpus and independent validator outputs.
