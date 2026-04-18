//! RocksDB-backed DAG storage — skeleton.

use std::path::Path;

pub struct DagStore;

impl DagStore {
    pub fn open(_path: &Path) -> anyhow::Result<Self> { Ok(DagStore) }
}
