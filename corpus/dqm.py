"""
corpus/dqm.py — Data Quality Metric (DQM) scoring and Φ-based pricing.

DataBundle models a corpus of engineering case chains and computes:
  Ψb (psi_bundle) = cardinality × diversity × chain_mean × transfer_logistics
  Φ (phi_price)   = Ψb × base_price × 1.618   (golden-ratio premium)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DataBundle:
    """A scored collection of engineering case chains ready for licensing.

    Args:
        chains: List of per-chain confidence scores (0–1 each).
        domains: Unique domain labels present in the bundle.
        transfer_logistics_factor: 1.0 = frictionless delivery (default);
            lower for large bundles requiring manual transfer coordination.
    """

    chains: List[float] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    transfer_logistics_factor: float = 1.0

    # ── Core metrics ─────────────────────────────────────────────────────────

    @property
    def cardinality(self) -> int:
        """Number of chains (cases) in the bundle."""
        return len(self.chains)

    @property
    def diversity(self) -> float:
        """Normalised domain diversity: unique_domains / cardinality (capped at 1.0)."""
        if not self.chains:
            return 0.0
        unique = len(set(d.strip().lower() for d in self.domains))
        return min(unique / self.cardinality, 1.0)

    @property
    def chain_mean(self) -> float:
        """Mean confidence score across all chains."""
        if not self.chains:
            return 0.0
        return sum(self.chains) / len(self.chains)

    # ── Ψb bundle score ───────────────────────────────────────────────────────

    def psi_bundle(self) -> float:
        """Ψb = cardinality × diversity × chain_mean × transfer_logistics_factor."""
        return (
            self.cardinality
            * self.diversity
            * self.chain_mean
            * self.transfer_logistics_factor
        )

    # ── Φ pricing ─────────────────────────────────────────────────────────────

    def phi_price(self, base: float = 500.0) -> float:
        """Φ = Ψb × base × φ   (φ = 1.618 golden ratio).

        Args:
            base: Base price per unit of Ψb (default EUR 500).

        Returns: Recommended price in EUR.
        """
        phi = (1 + math.sqrt(5)) / 2  # golden ratio ≈ 1.61803…
        return self.psi_bundle() * base * phi

    def estimated_price_eur(self, base: float = 500.0) -> str:
        """Human-readable price recommendation."""
        psi = self.psi_bundle()
        price = self.phi_price(base)
        return (
            f"DataBundle — {self.cardinality} chains | "
            f"{len(set(self.domains))} domains\n"
            f"  Ψb (bundle score) : {psi:.2f}\n"
            f"  Φ-price (EUR)     : {price:,.0f} €\n"
            f"  Base unit price   : {base:.0f} €/Ψb × φ"
        )


# ── Convenience builder ───────────────────────────────────────────────────────

def bundle_from_jsonl(jsonl_path: str, base_price: float = 500.0) -> DataBundle:
    """Build a DataBundle from a corpus JSONL file and print the price estimate.

    Each JSONL line must have 'dqm.final_score' and 'domain' fields.
    """
    import json

    chains: List[float] = []
    domains: List[str] = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            dqm = record.get("dqm", {})
            chains.append(float(dqm.get("final_score", 0.0)))
            domains.append(str(record.get("domain", "unknown")))

    bundle = DataBundle(chains=chains, domains=domains)
    print(bundle.estimated_price_eur(base_price))
    return bundle


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        bundle_from_jsonl(sys.argv[1])
    else:
        # Demo with synthetic values.
        demo = DataBundle(
            chains=[0.82, 0.91, 0.75, 0.88, 0.79] * 200,
            domains=["health", "engineering", "revenue", "governance", "cna_cli"] * 200,
        )
        print(demo.estimated_price_eur())
