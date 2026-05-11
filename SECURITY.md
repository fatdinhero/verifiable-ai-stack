# Security policy

`verifiable-ai-stack` contains governance, compliance, validation, and local-first AI components. Treat security issues conservatively, especially anything involving secrets, user data, audit reports, validator integrity, or compliance decisions.

## Supported scope

Security reports may involve:

- secret exposure or credential leakage,
- unsafe handling of governance audit reports,
- bypasses of the governance audit quality gate,
- validator-score manipulation or report-signature defects,
- MCP tool execution risks,
- unsafe default behavior in privacy-sensitive workflows,
- dependency vulnerabilities in Python, Rust, Node, or MCP components.

Component-specific issues should still be reported at the monorepo level when they affect cross-component trust boundaries.

## Reporting vulnerabilities

Do **not** create a public issue for a vulnerability.

Report privately to:

- Email: `datalabel.tech@gmail.com`

Include:

1. affected path or component,
2. impact and exploit scenario,
3. reproduction steps,
4. suggested mitigation if known,
5. whether secrets, personal data, or governance reports were exposed.

## Secret handling

- Never commit `.env`, API keys, signing keys, HMAC keys, private validator credentials, or MCP tokens.
- Governance audit signing uses `GOVERNANCE_AUDIT_HMAC_KEY`; keep it in CI secrets only.
- If a secret is committed, rotate it immediately and treat the commit history as compromised.

## Audit integrity expectations

Governance audit reports should remain reproducible and inspectable:

- `source_sha256` must match `cognitum/governance/masterplan.yaml`.
- each claim must include `original_claim_sha256`,
- `integrity.report_payload_sha256` must cover the unsigned report payload,
- signatures must be generated from secrets outside Git.

## Dependency hygiene

Use pinned lockfiles where component ecosystems already provide them. Review dependency audit warnings before production use, especially in compliance and MCP execution paths.

## Disclosure posture

This repository is currently evolving rapidly. Security fixes that affect governance, validation, or compliance should be prioritized over feature work and should include tests or reproducible smoke checks.
