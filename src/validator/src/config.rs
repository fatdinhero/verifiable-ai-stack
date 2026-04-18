//! Protocol configuration.

use std::path::PathBuf;

#[derive(Clone, Debug)]
pub struct ProtocolConfig {
    pub node_id: String,
    pub data_dir: PathBuf,
    pub theta_min: f64,
    pub psi_min:   f64,
    pub tau:       f64,
}

impl ProtocolConfig {
    pub fn load() -> anyhow::Result<Self> {
        Ok(Self {
            node_id: std::env::var("AP_NODE_ID").unwrap_or_else(|_| "default".into()),
            data_dir: PathBuf::from(std::env::var("AP_DATA_DIR").unwrap_or_else(|_| "./data".into())),
            theta_min: 0.6,
            psi_min:   0.7,
            tau:       0.7,
        })
    }
}
