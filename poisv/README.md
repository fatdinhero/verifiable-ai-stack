# PoISV: Proof of Independent Semantic Validation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19642292.svg)](https://doi.org/10.5281/zenodo.19642292)
![Bitcoin Block](https://img.shields.io/badge/Bitcoin_Block-945622-orange)
![License](https://img.shields.io/badge/license--docs-CC--BY--4.0-blue)

> **Scientific foundation for AgentsProtocol.**

This repository is the formally archived scientific layer:
three whitepapers (Meta-Bell Theory, Proof of WiseWork v2, PoISV v1.0),
their reference implementations, and interactive Jupyter notebooks.

## Architecture

```
    Meta-Bell Theory       [measure-theoretic foundation]
          |
          |  Psi entanglement measure
          v
    Proof of WiseWork       [truth x context x relevance x ethics]
          |
          |  W(i) = T C R E
          v
    PoISV                   [operational protocol]
          |
          |  S_con + Psi + GHOSTDAG ordering
          v
    AgentsProtocol          [application layer]
```

## Source Archive

Hashes correspond to the SHA256SUMS manifest inside the published ZIP.
All 18 documents (DE/EN/TR) are anchored under the single Zenodo DOI
**10.5281/zenodo.19642292**.

| File                                    | Language |
|-----------------------------------------|----------|
| `AgentsProtocol_Whitepaper_v1.2_{DE,EN,TR}.pdf` | DE/EN/TR |
| `AgentsProtocol_ExecutiveSummary_{DE,EN,TR}.pdf`| DE/EN/TR |
| `AgentsProtocol_DevDocs.pdf`            | DE (EN translation in repo) |
| `AgentsProtocol_Legal_Governance.pdf`   | DE       |
| `MetaBell_Theorie_v1_{DE,EN,TR}.pdf`    | DE/EN/TR |
| `PoWW_Whitepaper_v2_{DE,EN,TR}.pdf`     | DE/EN/TR |
| `PoISV_Whitepaper_v1.0_{DE,EN,TR}.pdf`  | DE/EN/TR |
| [Bell-SPVU Paper](https://doi.org/10.5281/zenodo.19656679) — DOI 10.5281/zenodo.19656679 | EN |

SHA256 (Bell-SPVU Paper): `ac0b646d6889bd94ae676302086de0f42af6d7185da4aa2a4c58fb068eab2f45`

## Three Reference Packages

- `meta-bell/`  — Psi entanglement measure (measure-theoretic).
- `poww/`       — WiseScore T x C x R x E + Gambler's Ruin probability.
- `poisv/`      — Full acceptance rule, block weight, DAG wrapper.

## Live Sites

- <https://poisv.com>
- <https://agentsprotocol.org>

## License

Documentation and notebooks: CC BY 4.0. Code snippets embedded in
notebooks: Apache-2.0 (see `LICENSE-CODE`).
