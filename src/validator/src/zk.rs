//! zkVM interface — skeleton.
//!
//! The protocol is zkVM-agnostic. Feature flags select the backend:
//!   `--features zkvm-risc0`  → RISC Zero
//!   `--features zkvm-nexus`  → Nexus zkVM
//!   `--features zkvm-sp1`    → SP1 (planned)

pub trait ZkBackend {
    fn prove(&self, guest_elf: &[u8], input: &[u8]) -> anyhow::Result<Vec<u8>>;
    fn verify(&self, receipt: &[u8], journal: &[u8]) -> anyhow::Result<bool>;
}
