"""Pydantic models mirroring claim-v1.0.json.

Reference: AgentsProtocol DevDocs v1.0, Section 2 (Listing 2/3).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")


class Entity(BaseModel):
    name: str
    type: str
    uri: Optional[str] = None


class Evidence(BaseModel):
    type: str
    uri: str
    timestamp: Optional[datetime] = None


class ClaimContext(BaseModel):
    domain: Optional[str] = None
    knowledgeCorpus: Optional[str] = Field(
        default=None, description="IPFS CID (as URI) of knowledge corpus kappa"
    )


class ClaimPayload(BaseModel):
    statement: str
    entities: List[Entity] = Field(default_factory=list)
    predicate: str
    value: Dict[str, Any]
    evidence: List[Evidence] = Field(default_factory=list)
    context: Optional[ClaimContext] = None


class Claim(BaseModel):
    protocol: Literal["agentsprotocol"] = "agentsprotocol"
    version: str
    type: Literal["claim"] = "claim"
    id: str = Field(description="SHA-256 hash of serialised payload")
    timestamp: datetime
    submitter: str = Field(description="Ed25519 public key (hex)")
    signature: str = Field(description="Ed25519 signature over id")
    payload: ClaimPayload

    @field_validator("version")
    @classmethod
    def _check_version(cls, v: str) -> str:
        if not _VERSION_RE.match(v):
            raise ValueError("version must match major.minor pattern")
        return v


class ValidatorOutput(BaseModel):
    validator_pubkey: str
    claim_id: str
    s_con: float = Field(ge=0.0, le=1.0)
    stake: float = Field(ge=0.0)
    signature: str


class BlockHeader(BaseModel):
    protocol_version: str
    parent_hashes: List[str]
    claims_merkle_root: str
    zk_proof_hash: str
    timestamp: datetime
    psi: float = Field(ge=0.0, le=1.0)
    cumulative_weight: float = Field(ge=0.0)


class Block(BaseModel):
    header: BlockHeader
    claims: List[Claim]
    validator_outputs: List[ValidatorOutput] = Field(default_factory=list)
    coinbase_recipient: Optional[str] = None
    fees: List[Dict[str, Any]] = Field(default_factory=list)

    def mean_s_con(self) -> float:
        scores = [v.s_con for v in self.validator_outputs]
        return sum(scores) / len(scores) if scores else 0.0


class ControlTask(BaseModel):
    id: str
    statement: str
    expectedScore: float = Field(ge=0.0, le=1.0)


class ControlSet(BaseModel):
    controlSetId: str
    genesisHash: str
    claims: List[ControlTask]
