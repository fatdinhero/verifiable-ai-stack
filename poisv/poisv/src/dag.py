"""Minimal DAG for PoISV offline tests — nodes carry (psi, s_cons)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from agentsprotocol.validator import block_weight

@dataclass
class DagBlock:
    id: str
    parents: List[str] = field(default_factory=list)
    psi: float = 1.0
    s_cons: List[float] = field(default_factory=list)
    @property
    def weight(self) -> float:
        return block_weight(self.psi, self.s_cons)

class Dag:
    def __init__(self) -> None:
        self.blocks: Dict[str, DagBlock] = {}
    def add(self, block: DagBlock) -> None:
        self.blocks[block.id] = block
    def heaviest_path(self) -> List[str]:
        # simple topological heaviest-weight selection
        order = sorted(self.blocks.values(),
                       key=lambda b: (-b.weight, b.id))
        return [b.id for b in order]
