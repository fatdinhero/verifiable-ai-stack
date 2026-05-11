//! Protocol configuration — loaded from environment variables with defaults.
//!
//! All tunable parameters live here so BlockProducer, ClaimMempool, and
//! the acceptance rule never contain hardcoded constants.

use std::path::PathBuf;

#[derive(Clone, Debug)]
pub struct ProtocolConfig {
    // -- Node identity --------------------------------------------------------
    pub node_id: String,
    pub data_dir: PathBuf,

    // -- Validation thresholds (DevDocs §8) -----------------------------------
    /// S_con acceptance threshold τ ∈ [0, 1). Claims below this score zero.
    pub tau: f64,
    /// Mean S_con threshold θ_min for block acceptance.
    pub theta_min: f64,
    /// Psi threshold Ψ_min for block acceptance.
    pub psi_min: f64,

    // -- Block production -----------------------------------------------------
    /// Minimum claims before the BlockProducer assembles a block.
    pub min_claims_per_block: usize,
    /// Maximum seconds to wait before producing a block regardless of count.
    pub block_timeout_secs: u64,
    /// Maximum claims per block.
    pub max_claims_per_block: usize,

    // -- GHOSTDAG -------------------------------------------------------------
    /// Number of parents selected per block (k parameter).
    pub ghostdag_k: usize,
    /// How many recent blocks to consider when selecting parents.
    pub parent_candidate_window: usize,

    // -- Network --------------------------------------------------------------
    /// Gossipsub topics this node subscribes to.
    pub topics: Vec<String>,
    /// P2P listen address.
    pub listen_addr: String,
    /// JSON-RPC listen address.
    pub rpc_addr: String,
    /// URL of the embedding sidecar (feature = "http-embed").
    /// e.g. "http://embed:8000/embed"
    pub embed_url: String,
    /// Comma-separated list of bootstrap peer multiaddrs.
    /// e.g. "/ip4/1.2.3.4/tcp/9000/p2p/12D3Koo..."
    pub bootstrap_peers: Vec<String>,
}

impl ProtocolConfig {
    pub fn load() -> anyhow::Result<Self> {
        let topics = vec![
            "/agentsprotocol/claims/1.0.0".to_string(),
            "/agentsprotocol/blocks/1.0.0".to_string(),
            "/agentsprotocol/control/1.0.0".to_string(),
            "/agentsprotocol/peers/1.0.0".to_string(),
        ];

        Ok(Self {
            node_id: std::env::var("AP_NODE_ID")
                .unwrap_or_else(|_| "default".into()),
            data_dir: PathBuf::from(
                std::env::var("AP_DATA_DIR").unwrap_or_else(|_| "./data".into()),
            ),

            tau: parse_env("AP_TAU", 0.0),
            theta_min: parse_env("AP_THETA_MIN", 0.6),
            psi_min: parse_env("AP_PSI_MIN", 0.7),

            min_claims_per_block: parse_env("AP_MIN_CLAIMS", 3usize),
            block_timeout_secs: parse_env("AP_BLOCK_TIMEOUT_SECS", 30u64),
            max_claims_per_block: parse_env("AP_MAX_CLAIMS_PER_BLOCK", 64usize),

            ghostdag_k: parse_env("AP_GHOSTDAG_K", 5usize),
            parent_candidate_window: parse_env("AP_PARENT_WINDOW", 100usize),

            topics,
            listen_addr: std::env::var("AP_LISTEN_ADDR")
                .unwrap_or_else(|_| "/ip4/0.0.0.0/tcp/0".into()),
            rpc_addr: std::env::var("AP_RPC_ADDR")
                .unwrap_or_else(|_| "0.0.0.0:8545".into()),
            embed_url: std::env::var("AP_EMBED_URL")
                .unwrap_or_else(|_| "http://localhost:8000/embed".into()),
            bootstrap_peers: std::env::var("AP_BOOTSTRAP_PEERS")
                .unwrap_or_default()
                .split(',')
                .map(str::trim)
                .filter(|s| !s.is_empty())
                .map(String::from)
                .collect(),
        })
    }
}

/// Parse an env var as `T`, falling back to `default` on missing or parse error.
fn parse_env<T>(key: &str, default: T) -> T
where
    T: std::str::FromStr + Copy,
{
    std::env::var(key)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}
