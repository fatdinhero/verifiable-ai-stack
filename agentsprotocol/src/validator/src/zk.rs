//! ZK proof abstraction for AgentsProtocol.
//!
//! This module defines the ZkBackend trait and ZkProof/ZkBlockInput types.
//!
//! # Backends
//!
//! | Feature flag    | Backend          | Type                        |
//! |-----------------|------------------|-----------------------------|
//! | (default)       | MockZkBackend    | SHA-256 deterministic commitment |
//! | zkvm-risc0      | Risc0ZkBackend   | RISC Zero receipt (skeleton) |
//!
//! # Important
//!
//! The default MockZkBackend is NOT a cryptographic zero-knowledge proof.
//! It is a deterministic commitment used for development and CI.
//! Real zkVM backends are experimental and feature-gated.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

// -- Public input schema ------------------------------------------------------

/// Canonical input to the ZK proof for a block.
///
/// All fields are deterministic and sorted to ensure reproducibility.
/// Floats are serialised as fixed-precision strings to avoid rounding issues.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ZkBlockInput {
    /// Protocol identifier — must be "agentsprotocol-zk-v1"
    pub protocol_version: String,
    /// Validator binary version from Cargo.toml
    pub validator_version: String,
    /// SHA-256 hex hash of the block
    pub block_hash: String,
    /// Sorted list of claim IDs included in the block
    pub claim_ids: Vec<String>,
    /// Mean S_con score, serialised as 6 decimal places
    pub s_con: String,
    /// Psi score, serialised as 6 decimal places
    pub psi: String,
}

impl ZkBlockInput {
    pub fn new(
        block_hash: &str,
        mut claim_ids: Vec<String>,
        s_con: f64,
        psi: f64,
    ) -> Self {
        claim_ids.sort();
        Self {
            protocol_version: "agentsprotocol-zk-v1".into(),
            validator_version: env!("CARGO_PKG_VERSION").into(),
            block_hash: block_hash.to_string(),
            claim_ids,
            s_con: format!("{s_con:.6}"),
            psi: format!("{psi:.6}"),
        }
    }

    /// Canonical JSON bytes for hashing — keys sorted, no whitespace.
    pub fn canonical_bytes(&self) -> Vec<u8> {
        // Manual construction guarantees stable key order.
        let json = format!(
            r#"{{"block_hash":{},"claim_ids":{},"psi":{},"protocol_version":{},"s_con":{},"validator_version":{}}}"#,
            serde_json::to_string(&self.block_hash).unwrap(),
            serde_json::to_string(&self.claim_ids).unwrap(),
            serde_json::to_string(&self.psi).unwrap(),
            serde_json::to_string(&self.protocol_version).unwrap(),
            serde_json::to_string(&self.s_con).unwrap(),
            serde_json::to_string(&self.validator_version).unwrap(),
        );
        json.into_bytes()
    }
}

// -- ZkProof ------------------------------------------------------------------

/// A proof (or commitment) attached to a StoredBlock.
///
/// The `backend` field identifies the proof type so verifiers can choose
/// the correct verification path.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ZkProof {
    /// Backend identifier: "mock-sha256" | "risc0" | "sp1" | "nexus"
    pub backend: String,
    /// Human-readable proof type label
    pub proof_type: String,
    /// Hex-encoded commitment or receipt
    pub commitment: String,
    /// SHA-256 hex of the canonical ZkBlockInput JSON
    pub public_inputs_hash: String,
    /// Whether the proof was verified at creation time
    pub verified: bool,
}

// -- ZkError ------------------------------------------------------------------

#[derive(Debug, thiserror::Error)]
pub enum ZkError {
    #[error("proof generation failed: {0}")]
    ProveFailed(String),
    #[error("proof verification failed: {0}")]
    VerifyFailed(String),
    #[error("input serialisation error: {0}")]
    InputError(String),
}

// -- ZkBackend trait ----------------------------------------------------------

pub trait ZkBackend: Send + Sync {
    /// Generate a proof (or commitment) for the given block input.
    fn prove_block(&self, input: &ZkBlockInput) -> Result<ZkProof, ZkError>;

    /// Verify a proof against the given block input.
    fn verify_block(&self, input: &ZkBlockInput, proof: &ZkProof) -> Result<bool, ZkError>;

    /// Human-readable backend name for logging.
    fn name(&self) -> &'static str;
}

// -- MockZkBackend ------------------------------------------------------------

/// Development commitment backend.
///
/// NOT a cryptographic zero-knowledge proof.
/// Produces a deterministic SHA-256 commitment over the canonical block input.
/// Suitable for development, testing, and CI only.
pub struct MockZkBackend;

impl ZkBackend for MockZkBackend {
    fn name(&self) -> &'static str {
        "mock-sha256"
    }

    fn prove_block(&self, input: &ZkBlockInput) -> Result<ZkProof, ZkError> {
        let canonical = input.canonical_bytes();
        let public_inputs_hash = format!("{:x}", Sha256::digest(&canonical));
        // Commitment = SHA-256(SHA-256(canonical)) — double hash for separation
        let commitment = format!("{:x}", Sha256::digest(public_inputs_hash.as_bytes()));

        Ok(ZkProof {
            backend: "mock-sha256".into(),
            proof_type: "development_commitment".into(),
            commitment,
            public_inputs_hash,
            verified: true,
        })
    }

    fn verify_block(&self, input: &ZkBlockInput, proof: &ZkProof) -> Result<bool, ZkError> {
        if proof.backend != "mock-sha256" {
            return Err(ZkError::VerifyFailed(format!(
                "backend mismatch: expected mock-sha256, got {}",
                proof.backend
            )));
        }
        // Recompute and compare
        let canonical = input.canonical_bytes();
        let expected_inputs_hash = format!("{:x}", Sha256::digest(&canonical));
        let expected_commitment = format!("{:x}", Sha256::digest(expected_inputs_hash.as_bytes()));

        Ok(proof.public_inputs_hash == expected_inputs_hash
            && proof.commitment == expected_commitment)
    }
}

// -- Risc0ZkBackend skeleton --------------------------------------------------

/// RISC Zero backend skeleton.
///
/// Requires `--features zkvm-risc0`. Not built in CI.
/// The guest ELF is a stub until the guest program is implemented.
#[cfg(feature = "zkvm-risc0")]
pub struct Risc0ZkBackend;

#[cfg(feature = "zkvm-risc0")]
impl ZkBackend for Risc0ZkBackend {
    fn name(&self) -> &'static str {
        "risc0"
    }

    fn prove_block(&self, _input: &ZkBlockInput) -> Result<ZkProof, ZkError> {
        // TODO: compile guest ELF and call risc0_zkvm::default_prover()
        Err(ZkError::ProveFailed(
            "RISC Zero guest ELF not yet implemented".into(),
        ))
    }

    fn verify_block(&self, _input: &ZkBlockInput, _proof: &ZkProof) -> Result<bool, ZkError> {
        // TODO: deserialise receipt and call receipt.verify(IMAGE_ID)
        Err(ZkError::VerifyFailed(
            "RISC Zero guest ELF not yet implemented".into(),
        ))
    }
}

// -- Tests --------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_input() -> ZkBlockInput {
        ZkBlockInput::new(
            "abc123",
            vec!["claim_b".into(), "claim_a".into()],
            0.842100,
            0.731200,
        )
    }

    #[test]
    fn claim_ids_are_sorted() {
        let input = sample_input();
        assert_eq!(input.claim_ids, vec!["claim_a", "claim_b"]);
    }

    #[test]
    fn canonical_bytes_are_deterministic() {
        let a = sample_input().canonical_bytes();
        let b = sample_input().canonical_bytes();
        assert_eq!(a, b);
    }

    #[test]
    fn mock_proof_is_deterministic() {
        let backend = MockZkBackend;
        let input = sample_input();
        let p1 = backend.prove_block(&input).unwrap();
        let p2 = backend.prove_block(&input).unwrap();
        assert_eq!(p1.commitment, p2.commitment);
        assert_eq!(p1.public_inputs_hash, p2.public_inputs_hash);
    }

    #[test]
    fn mock_verify_accepts_valid_proof() {
        let backend = MockZkBackend;
        let input = sample_input();
        let proof = backend.prove_block(&input).unwrap();
        assert!(backend.verify_block(&input, &proof).unwrap());
    }

    #[test]
    fn mock_verify_rejects_tampered_psi() {
        let backend = MockZkBackend;
        let input = sample_input();
        let proof = backend.prove_block(&input).unwrap();

        // Tamper: change psi
        let mut tampered = input.clone();
        tampered.psi = "0.999999".into();
        assert!(!backend.verify_block(&tampered, &proof).unwrap());
    }

    #[test]
    fn mock_verify_rejects_tampered_commitment() {
        let backend = MockZkBackend;
        let input = sample_input();
        let mut proof = backend.prove_block(&input).unwrap();
        proof.commitment = "deadbeef".into();
        assert!(!backend.verify_block(&input, &proof).unwrap());
    }

    #[test]
    fn mock_proof_backend_label_is_not_zk() {
        let backend = MockZkBackend;
        let proof = backend.prove_block(&sample_input()).unwrap();
        assert_eq!(proof.backend, "mock-sha256");
        assert_eq!(proof.proof_type, "development_commitment");
    }

    #[test]
    fn stored_block_deserializes_without_zk_proof() {
        // Simulates reading an old StoredBlock that has no zk_proof field.
        let json = r#"{
            "hash": "h1",
            "parent_hashes": [],
            "timestamp": "2026-01-01T00:00:00Z",
            "psi": 1.0,
            "cumulative_weight": 1.0,
            "claim_ids": []
        }"#;
        let block: crate::storage::StoredBlock = serde_json::from_str(json).unwrap();
        assert!(block.zk_proof.is_none());
    }
}
