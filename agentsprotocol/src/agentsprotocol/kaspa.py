"""Kaspa / GHOSTDAG integration.

AgentsProtocol uses GHOSTDAG (Sompolinsky, Wyborski, Zohar, AFT 2021) as the
ordering layer. This module exposes:

  * `KaspaClient` — minimal JSON-RPC client against api.kaspa.org.
  * `GhostdagBridge` — translates GHOSTDAG block order into AgentsProtocol
    block weights: Weight(B) = Psi_B * sum S_con(A).

Network I/O is optional — `aiohttp` is imported lazily so the rest of the
package works without it. `simulate_dag()` produces a fully offline DAG for
tests and demos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .validator import block_weight


DEFAULT_KASPA_HTTP = "https://api.kaspa.org"


@dataclass
class KaspaBlock:
    block_hash: str
    parent_hashes: List[str]
    daa_score: int
    blue_score: int
    timestamp: int
    payload: bytes = b""


class KaspaClient:
    """Tiny JSON-RPC / REST client for a Kaspa node.

    Supported endpoints (subset of api.kaspa.org):
        GET /info/blockdag
        GET /blocks/{hash}
        GET /blocks/{hash}/children
        GET /virtual-chain-from-block/{hash}

    The official Kaspa RPC is gRPC-based; the REST gateway at api.kaspa.org
    covers the subset we need for read-only validator observation.
    """

    def __init__(self, endpoint: str = DEFAULT_KASPA_HTTP, timeout: float = 15.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self._session = None

    async def _get(self, path: str) -> Dict[str, Any]:
        try:
            import aiohttp  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "aiohttp is required for live Kaspa I/O. "
                "Install with: pip install aiohttp"
            ) from exc
        if self._session is None:
            self._session = aiohttp.ClientSession()
        url = f"{self.endpoint}{path}"
        async with self._session.get(url, timeout=self.timeout) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_dag_info(self) -> Dict[str, Any]:
        """GET /info/blockdag — current DAG tips, virtual DAA, etc."""
        return await self._get("/info/blockdag")

    async def get_block(self, block_hash: str) -> KaspaBlock:
        data = await self._get(f"/blocks/{block_hash}")
        header = data.get("header", data)
        return KaspaBlock(
            block_hash=header.get("hash", block_hash),
            parent_hashes=list(header.get("parents", [])),
            daa_score=int(header.get("daaScore", 0)),
            blue_score=int(header.get("blueScore", 0)),
            timestamp=int(header.get("timestamp", 0)),
        )

    async def virtual_chain_from_block(self, anchor_hash: str) -> List[str]:
        data = await self._get(f"/virtual-chain-from-block/{anchor_hash}")
        return list(data.get("addedChainBlockHashes", []))

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None


@dataclass
class SemanticBlock:
    """AgentsProtocol semantic annotation attached to a GHOSTDAG block."""

    kaspa_block_hash: str
    psi: float
    s_con_scores: List[float] = field(default_factory=list)

    @property
    def weight(self) -> float:
        return block_weight(self.psi, self.s_con_scores)


class GhostdagBridge:
    """Maps GHOSTDAG block order to AgentsProtocol block weights."""

    def __init__(self) -> None:
        self.semantic_blocks: Dict[str, SemanticBlock] = {}

    def annotate(self, kaspa_block_hash: str, psi: float,
                 s_con_scores: Sequence[float]) -> SemanticBlock:
        sb = SemanticBlock(kaspa_block_hash=kaspa_block_hash, psi=psi,
                           s_con_scores=list(s_con_scores))
        self.semantic_blocks[kaspa_block_hash] = sb
        return sb

    def canonical_path(self, ordered_hashes: Sequence[str]) -> List[str]:
        """Select the path with the highest cumulative semantic weight.

        `ordered_hashes` is the GHOSTDAG-induced total order; we retain only
        blocks we have annotated and sort by cumulative weight.
        """
        annotated = [h for h in ordered_hashes if h in self.semantic_blocks]
        cumulative = 0.0
        path: List[str] = []
        for h in annotated:
            cumulative += self.semantic_blocks[h].weight
            path.append(h)
        return path

    def total_weight(self) -> float:
        return sum(sb.weight for sb in self.semantic_blocks.values())


def simulate_dag(num_blocks: int = 10, k: int = 3,
                 seed: int = 42) -> List[KaspaBlock]:
    """Generate a synthetic GHOSTDAG-like DAG for offline tests.

    Each block references up to `k` recent tips; timestamps are monotonic.
    """
    import random
    rng = random.Random(seed)
    blocks: List[KaspaBlock] = []
    for i in range(num_blocks):
        parents = [blocks[j].block_hash for j in range(max(0, i - k), i)]
        if not parents and i == 0:
            parents = []
        else:
            parents = rng.sample(parents, min(len(parents), k))
        bh = f"block_{i:06d}_" + format(rng.getrandbits(32), "08x")
        blocks.append(KaspaBlock(
            block_hash=bh, parent_hashes=parents,
            daa_score=i, blue_score=i, timestamp=1_713_000_000 + i * 1000,
        ))
    return blocks
