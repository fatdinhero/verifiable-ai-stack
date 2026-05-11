//! RocksDB-backed DAG storage.
//!
//! Two column families:
//!   "claims" — key: claim_id (hex string)  → value: JSON-serialised StoredClaim
//!   "blocks" — key: block_hash (hex string) → value: JSON-serialised StoredBlock
//!
//! All public types derive serde::{Serialize, Deserialize} so they can be
//! round-tripped through JSON without a separate schema layer.

use std::path::Path;

use anyhow::{Context, Result};
use rocksdb::{ColumnFamilyDescriptor, Options, DB};
use serde::{Deserialize, Serialize};

// -- Stored types -------------------------------------------------------------

/// Minimal claim record persisted to storage.
/// Fields mirror the JSON schema (claim-v1.0.json) required properties.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredClaim {
    pub id: String,
    pub protocol: String,
    pub version: String,
    pub timestamp: String,
    pub submitter: String,
    pub signature: String,
    pub statement: String,
    /// Raw JSON payload — preserved verbatim for signature verification.
    pub payload_json: String,
}

/// Minimal block record persisted to storage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredBlock {
    pub hash: String,
    pub parent_hashes: Vec<String>,
    pub timestamp: String,
    pub psi: f64,
    pub cumulative_weight: f64,
    pub claim_ids: Vec<String>,
}

// -- Column family names ------------------------------------------------------

const CF_CLAIMS: &str = "claims";
const CF_BLOCKS: &str = "blocks";

// -- DagStore -----------------------------------------------------------------

pub struct DagStore {
    db: DB,
}

impl DagStore {
    /// Open (or create) the RocksDB database at `path`.
    pub fn open(path: &Path) -> Result<Self> {
        let mut opts = Options::default();
        opts.create_if_missing(true);
        opts.create_missing_column_families(true);

        let cf_opts = Options::default();
        let cfs = vec![
            ColumnFamilyDescriptor::new(CF_CLAIMS, cf_opts.clone()),
            ColumnFamilyDescriptor::new(CF_BLOCKS, cf_opts),
        ];

        let db = DB::open_cf_descriptors(&opts, path, cfs)
            .with_context(|| format!("failed to open RocksDB at {}", path.display()))?;

        Ok(Self { db })
    }

    // -- Claims ---------------------------------------------------------------

    /// Persist a claim. Overwrites any existing record with the same id.
    pub fn save_claim(&self, claim: &StoredClaim) -> Result<()> {
        let cf = self
            .db
            .cf_handle(CF_CLAIMS)
            .context("claims column family not found")?;
        let value = serde_json::to_vec(claim).context("failed to serialise claim")?;
        self.db
            .put_cf(&cf, claim.id.as_bytes(), &value)
            .context("RocksDB put_cf failed for claim")?;
        Ok(())
    }

    /// Retrieve a claim by id. Returns `None` if not found.
    pub fn get_claim(&self, claim_id: &str) -> Result<Option<StoredClaim>> {
        let cf = self
            .db
            .cf_handle(CF_CLAIMS)
            .context("claims column family not found")?;
        match self.db.get_cf(&cf, claim_id.as_bytes())? {
            None => Ok(None),
            Some(bytes) => {
                let claim = serde_json::from_slice(&bytes)
                    .context("failed to deserialise claim")?;
                Ok(Some(claim))
            }
        }
    }

    // -- Blocks ---------------------------------------------------------------

    /// Persist a block. Overwrites any existing record with the same hash.
    pub fn save_block(&self, block: &StoredBlock) -> Result<()> {
        let cf = self
            .db
            .cf_handle(CF_BLOCKS)
            .context("blocks column family not found")?;
        let value = serde_json::to_vec(block).context("failed to serialise block")?;
        self.db
            .put_cf(&cf, block.hash.as_bytes(), &value)
            .context("RocksDB put_cf failed for block")?;
        Ok(())
    }

    /// Retrieve a block by hash. Returns `None` if not found.
    pub fn get_block(&self, block_hash: &str) -> Result<Option<StoredBlock>> {
        let cf = self
            .db
            .cf_handle(CF_BLOCKS)
            .context("blocks column family not found")?;
        match self.db.get_cf(&cf, block_hash.as_bytes())? {
            None => Ok(None),
            Some(bytes) => {
                let block = serde_json::from_slice(&bytes)
                    .context("failed to deserialise block")?;
                Ok(Some(block))
            }
        }
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

    fn sample_block(hash: &str) -> StoredBlock {
        StoredBlock {
            hash: hash.to_string(),
            parent_hashes: vec!["0xparent".to_string()],
            timestamp: "2026-04-18T14:31:00Z".to_string(),
            psi: 0.85,
            cumulative_weight: 12.5,
            claim_ids: vec!["claim_abc".to_string()],
        }
    }

    #[test]
    fn claim_roundtrip() {
        let (store, _dir) = temp_store();
        let claim = sample_claim("claim_abc");
        store.save_claim(&claim).unwrap();
        let loaded = store.get_claim("claim_abc").unwrap().unwrap();
        assert_eq!(loaded.id, "claim_abc");
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
        let mut claim = sample_claim("claim_abc");
        store.save_claim(&claim).unwrap();
        claim.statement = "Updated statement.".to_string();
        store.save_claim(&claim).unwrap();
        let loaded = store.get_claim("claim_abc").unwrap().unwrap();
        assert_eq!(loaded.statement, "Updated statement.");
    }

    #[test]
    fn block_roundtrip() {
        let (store, _dir) = temp_store();
        let block = sample_block("0xblockhash");
        store.save_block(&block).unwrap();
        let loaded = store.get_block("0xblockhash").unwrap().unwrap();
        assert_eq!(loaded.hash, "0xblockhash");
        assert!((loaded.psi - 0.85).abs() < 1e-10);
        assert_eq!(loaded.claim_ids, vec!["claim_abc"]);
    }

    #[test]
    fn block_not_found_returns_none() {
        let (store, _dir) = temp_store();
        assert!(store.get_block("nonexistent").unwrap().is_none());
    }

    #[test]
    fn claims_and_blocks_independent() {
        // saving a claim must not affect block lookups and vice versa
        let (store, _dir) = temp_store();
        store.save_claim(&sample_claim("c1")).unwrap();
        assert!(store.get_block("c1").unwrap().is_none());
        store.save_block(&sample_block("b1")).unwrap();
        assert!(store.get_claim("b1").unwrap().is_none());
    }
}
