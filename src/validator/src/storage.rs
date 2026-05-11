//! sled-backed DAG storage.
//!
//! Two sled Trees (equivalent to RocksDB column families):
//!   "claims" — key: claim_id (UTF-8)  → value: JSON-serialised StoredClaim
//!   "blocks" — key: block_hash (UTF-8) → value: JSON-serialised StoredBlock

use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

// -- Stored types -------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredClaim {
    pub id: String,
    pub protocol: String,
    pub version: String,
    pub timestamp: String,
    pub submitter: String,
    pub signature: String,
    pub statement: String,
    pub payload_json: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredBlock {
    pub hash: String,
    pub parent_hashes: Vec<String>,
    pub timestamp: String,
    pub psi: f64,
    pub cumulative_weight: f64,
    pub claim_ids: Vec<String>,
    /// Development commitment or ZK proof attached at block production time.
    /// `None` for blocks produced before Phase 4 (backwards-compatible).
    #[serde(default)]
    pub zk_proof: Option<crate::zk::ZkProof>,
}

// -- DagStore -----------------------------------------------------------------

pub struct DagStore {
    claims: sled::Tree,
    blocks: sled::Tree,
}

impl DagStore {
    pub fn open(path: &Path) -> Result<Self> {
        let db = sled::open(path)
            .with_context(|| format!("failed to open sled at {}", path.display()))?;
        let claims = db.open_tree("claims").context("open claims tree")?;
        let blocks = db.open_tree("blocks").context("open blocks tree")?;
        Ok(Self { claims, blocks })
    }

    // -- Claims ---------------------------------------------------------------

    pub fn save_claim(&self, claim: &StoredClaim) -> Result<()> {
        let value = serde_json::to_vec(claim).context("serialise claim")?;
        self.claims
            .insert(claim.id.as_bytes(), value)
            .context("sled insert claim")?;
        Ok(())
    }

    pub fn get_claim(&self, claim_id: &str) -> Result<Option<StoredClaim>> {
        match self.claims.get(claim_id.as_bytes()).context("sled get claim")? {
            None => Ok(None),
            Some(bytes) => Ok(Some(
                serde_json::from_slice(&bytes).context("deserialise claim")?,
            )),
        }
    }

    // -- Blocks ---------------------------------------------------------------

    pub fn save_block(&self, block: &StoredBlock) -> Result<()> {
        let value = serde_json::to_vec(block).context("serialise block")?;
        self.blocks
            .insert(block.hash.as_bytes(), value)
            .context("sled insert block")?;
        Ok(())
    }

    pub fn get_block(&self, block_hash: &str) -> Result<Option<StoredBlock>> {
        match self.blocks.get(block_hash.as_bytes()).context("sled get block")? {
            None => Ok(None),
            Some(bytes) => Ok(Some(
                serde_json::from_slice(&bytes).context("deserialise block")?,
            )),
        }
    }

    /// Return up to `limit` blocks (reverse insertion order).
    pub fn list_recent_blocks(&self, limit: usize) -> Result<Vec<StoredBlock>> {
        let mut out = Vec::new();
        for item in self.blocks.iter().rev() {
            let (_key, value) = item.context("sled iter block")?;
            if let Ok(block) = serde_json::from_slice::<StoredBlock>(&value) {
                out.push(block);
            }
            if out.len() >= limit {
                break;
            }
        }
        Ok(out)
    }
}

// -- Tests --------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn temp_store() -> (DagStore, TempDir) {
        let dir = TempDir::new().unwrap();
        let store = DagStore::open(dir.path()).unwrap();
        (store, dir)
    }

    fn sample_claim(id: &str) -> StoredClaim {
        StoredClaim {
            id: id.to_string(),
            protocol: "agentsprotocol".to_string(),
            version: "1.0".to_string(),
            timestamp: "2026-04-18T14:30:00Z".to_string(),
            submitter: "0xdeadbeef".to_string(),
            signature: "0xsig".to_string(),
            statement: "The sky is blue.".to_string(),
            payload_json: r#"{"statement":"The sky is blue."}"#.to_string(),
        }
    }

    fn sample_block(hash: &str, weight: f64) -> StoredBlock {
        StoredBlock {
            hash: hash.to_string(),
            parent_hashes: vec![],
            timestamp: "2026-04-18T14:31:00Z".to_string(),
            psi: 1.0,
            cumulative_weight: weight,
            claim_ids: vec!["claim_abc".to_string()],
            zk_proof: None,
        }
    }

    #[test]
    fn claim_roundtrip() {
        let (store, _dir) = temp_store();
        store.save_claim(&sample_claim("c1")).unwrap();
        let loaded = store.get_claim("c1").unwrap().unwrap();
        assert_eq!(loaded.id, "c1");
        assert_eq!(loaded.statement, "The sky is blue.");
    }

    #[test]
    fn claim_not_found_returns_none() {
        let (store, _dir) = temp_store();
        assert!(store.get_claim("nonexistent").unwrap().is_none());
    }

    #[test]
    fn claim_overwrite() {
        let (store, _dir) = temp_store();
        let mut claim = sample_claim("c1");
        store.save_claim(&claim).unwrap();
        claim.statement = "Updated.".to_string();
        store.save_claim(&claim).unwrap();
        assert_eq!(store.get_claim("c1").unwrap().unwrap().statement, "Updated.");
    }

    #[test]
    fn block_roundtrip() {
        let (store, _dir) = temp_store();
        store.save_block(&sample_block("b1", 5.0)).unwrap();
        let loaded = store.get_block("b1").unwrap().unwrap();
        assert_eq!(loaded.hash, "b1");
        assert!((loaded.cumulative_weight - 5.0).abs() < 1e-10);
    }

    #[test]
    fn block_not_found_returns_none() {
        let (store, _dir) = temp_store();
        assert!(store.get_block("nonexistent").unwrap().is_none());
    }

    #[test]
    fn claims_and_blocks_independent() {
        let (store, _dir) = temp_store();
        store.save_claim(&sample_claim("c1")).unwrap();
        assert!(store.get_block("c1").unwrap().is_none());
        store.save_block(&sample_block("b1", 1.0)).unwrap();
        assert!(store.get_claim("b1").unwrap().is_none());
    }

    #[test]
    fn list_recent_blocks_ordered() {
        let (store, _dir) = temp_store();
        store.save_block(&sample_block("b1", 1.0)).unwrap();
        store.save_block(&sample_block("b2", 2.0)).unwrap();
        store.save_block(&sample_block("b3", 3.0)).unwrap();
        let blocks = store.list_recent_blocks(2).unwrap();
        assert_eq!(blocks.len(), 2);
    }
}
