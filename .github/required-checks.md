# Required GitHub checks

For GitHub branch protection, configure `main` so pull requests require the following status check before merge:

```text
Cognitum Governance Audit / governance-audit
```

Recommended branch protection settings:

- Require a pull request before merging.
- Require status checks to pass before merging.
- Require the `Cognitum Governance Audit / governance-audit` check.
- Require branches to be up to date before merging.
- Enable merge queue if available; the workflow listens to `merge_group`.
- Require CODEOWNERS review for governance, audit, compliance, protocol, and documentation paths.

The workflow file is:

```text
.github/workflows/governance-audit.yml
```

The check fails closed when `check_acceptance` rejects the report or when required report shape/integrity fields are missing.
