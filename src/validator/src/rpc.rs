//! JSON-RPC HTTP server (axum).
//!
//! Endpoints:
//!   POST /submit_claim  — validate signature, insert into ClaimMempool
//!   GET  /get_block/:hash — return StoredBlock as JSON
//!   GET  /status        — node_id, mempool_size, peer_count placeholder

use std::sync::Arc;

use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::Serialize;
use tower_http::cors::CorsLayer;
use tracing::{info, warn};

use crate::mempool::ClaimMempool;
use crate::storage::{DagStore, StoredClaim};
use crate::validation::verify_claim_signature;
use crate::zk::{MockZkBackend, ZkBackend, ZkBlockInput};

// -- Shared state -------------------------------------------------------------

#[derive(Clone)]
pub struct AppState {
    pub node_id: String,
    pub store: Arc<DagStore>,
    pub mempool: Arc<ClaimMempool>,
}

// -- Response types -----------------------------------------------------------

#[derive(Serialize)]
struct ErrorBody {
    error: String,
}

#[derive(Serialize)]
struct SubmitResponse {
    accepted: bool,
    claim_id: String,
    mempool_size: usize,
}

#[derive(Serialize)]
struct StatusResponse {
    node_id: String,
    mempool_size: usize,
    /// Placeholder — peer count requires access to the swarm (Phase 3).
    peer_count: usize,
}

#[derive(Serialize)]
struct VerifyBlockResponse {
    block_hash: String,
    has_proof: bool,
    backend: String,
    proof_type: String,
    verified: bool,
    /// Always present when backend is "mock-sha256".
    #[serde(skip_serializing_if = "Option::is_none")]
    warning: Option<String>,
}

// -- Handlers -----------------------------------------------------------------

/// POST /submit_claim
///
/// Body: StoredClaim JSON.
/// Verifies Ed25519 signature, then inserts into ClaimMempool.
async fn submit_claim(
    State(state): State<AppState>,
    Json(claim): Json<StoredClaim>,
) -> impl IntoResponse {
    match verify_claim_signature(&claim.submitter, &claim.signature, &claim.payload_json) {
        Ok(true) => {
            let id = claim.id.clone();
            state.mempool.insert(claim, &[]);
            let size = state.mempool.len();
            info!("RPC accepted claim {id} (mempool={size})");
            (
                StatusCode::OK,
                Json(serde_json::json!(SubmitResponse {
                    accepted: true,
                    claim_id: id,
                    mempool_size: size,
                })),
            )
        }
        Ok(false) => {
            warn!("RPC rejected claim {}: invalid signature", claim.id);
            (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!(ErrorBody {
                    error: "invalid Ed25519 signature".into(),
                })),
            )
        }
        Err(e) => {
            warn!("RPC sig verify error for {}: {e}", claim.id);
            (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!(ErrorBody {
                    error: format!("signature verification failed: {e}"),
                })),
            )
        }
    }
}

/// GET /get_block/:hash
async fn get_block(
    State(state): State<AppState>,
    Path(hash): Path<String>,
) -> impl IntoResponse {
    match state.store.get_block(&hash) {
        Ok(Some(block)) => (StatusCode::OK, Json(serde_json::to_value(block).unwrap())),
        Ok(None) => (
            StatusCode::NOT_FOUND,
            Json(serde_json::json!(ErrorBody {
                error: format!("block {hash} not found"),
            })),
        ),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!(ErrorBody {
                error: format!("storage error: {e}"),
            })),
        ),
    }
}

/// GET /verify_block/:hash
///
/// Loads the block from storage, re-derives the ZkBlockInput from its fields,
/// and verifies the attached commitment against it.
///
/// Response includes a `warning` field when the backend is "mock-sha256" to
/// make clear this is not a cryptographic zero-knowledge proof.
async fn verify_block(
    State(state): State<AppState>,
    Path(hash): Path<String>,
) -> impl IntoResponse {
    let block = match state.store.get_block(&hash) {
        Ok(Some(b)) => b,
        Ok(None) => {
            return (
                StatusCode::NOT_FOUND,
                Json(serde_json::json!(ErrorBody {
                    error: format!("block {hash} not found"),
                })),
            );
        }
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!(ErrorBody {
                    error: format!("storage error: {e}"),
                })),
            );
        }
    };

    let Some(proof) = &block.zk_proof else {
        return (
            StatusCode::OK,
            Json(serde_json::json!(VerifyBlockResponse {
                block_hash: hash,
                has_proof: false,
                backend: "none".into(),
                proof_type: "none".into(),
                verified: false,
                warning: Some("Block was produced before Phase 4 — no proof attached.".into()),
            })),
        );
    };

    // Re-derive ZkBlockInput from stored block fields
    let s_con_mean = if block.claim_ids.is_empty() {
        0.0
    } else {
        block.cumulative_weight / block.psi / block.claim_ids.len() as f64
    };
    let zk_input = ZkBlockInput::new(&block.hash, block.claim_ids.clone(), s_con_mean, block.psi);

    let (verified, warning) = match proof.backend.as_str() {
        "mock-sha256" => {
            let ok = MockZkBackend.verify_block(&zk_input, proof).unwrap_or(false);
            let w = Some(
                "Mock proof is not a cryptographic ZK proof. \
                 It is a development commitment (SHA-256 based)."
                    .into(),
            );
            (ok, w)
        }
        other => {
            warn!("verify_block: unknown backend {other}");
            (false, Some(format!("Unknown backend: {other}")))
        }
    };

    info!("verify_block {hash}: verified={verified} backend={}", proof.backend);
    (
        StatusCode::OK,
        Json(serde_json::json!(VerifyBlockResponse {
            block_hash: hash,
            has_proof: true,
            backend: proof.backend.clone(),
            proof_type: proof.proof_type.clone(),
            verified,
            warning,
        })),
    )
}

/// GET /status
async fn status(State(state): State<AppState>) -> impl IntoResponse {
    Json(StatusResponse {
        node_id: state.node_id.clone(),
        mempool_size: state.mempool.len(),
        peer_count: 0, // wired up in Phase 3 via AtomicUsize in AppState
    })
}

// -- Router -------------------------------------------------------------------

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/submit_claim", post(submit_claim))
        .route("/get_block/:hash", get(get_block))
        .route("/verify_block/:hash", get(verify_block))
        .route("/status", get(status))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

/// Start the RPC server on `addr`. Runs until the process exits.
pub async fn serve(addr: &str, state: AppState) -> anyhow::Result<()> {
    let listener = tokio::net::TcpListener::bind(addr).await?;
    info!("RPC server listening on {addr}");
    axum::serve(listener, router(state)).await?;
    Ok(())
}

// -- Tests --------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::{Request, StatusCode as AxumStatus};
    use http_body_util::BodyExt;
    use std::sync::Arc;
    use tempfile::TempDir;
    use tower::ServiceExt;

    use crate::config::ProtocolConfig;
    use crate::mempool::ClaimMempool;
    use crate::storage::{DagStore, StoredBlock};
    use crate::zk::{MockZkBackend, ZkBackend, ZkBlockInput};

    fn make_state(dir: &std::path::Path) -> AppState {
        let store = Arc::new(DagStore::open(dir).unwrap());
        let cfg = ProtocolConfig::load().unwrap();
        let mempool = Arc::new(ClaimMempool::new(cfg.clone()));
        AppState {
            node_id: "test-node".into(),
            store,
            mempool,
        }
    }

    fn make_block_with_proof(hash: &str) -> StoredBlock {
        let input = ZkBlockInput::new(hash, vec!["c1".into()], 0.9, 1.0);
        let proof = MockZkBackend.prove_block(&input).unwrap();
        StoredBlock {
            hash: hash.to_string(),
            parent_hashes: vec![],
            timestamp: "2026-01-01T00:00:00Z".into(),
            psi: 1.0,
            cumulative_weight: 0.9,
            claim_ids: vec!["c1".into()],
            zk_proof: Some(proof),
        }
    }

    #[tokio::test]
    async fn rpc_verify_block_returns_verified_true() {
        let dir = TempDir::new().unwrap();
        let state = make_state(dir.path());
        let block = make_block_with_proof("hash_abc");
        state.store.save_block(&block).unwrap();

        let app = router(state);
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/verify_block/hash_abc")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), AxumStatus::OK);
        let body = resp.into_body().collect().await.unwrap().to_bytes();
        let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(json["verified"], true);
        assert_eq!(json["has_proof"], true);
        assert_eq!(json["backend"], "mock-sha256");
    }

    #[tokio::test]
    async fn rpc_verify_block_returns_404_for_unknown_hash() {
        let dir = TempDir::new().unwrap();
        let state = make_state(dir.path());

        let app = router(state);
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/verify_block/nonexistent")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(resp.status(), AxumStatus::NOT_FOUND);
    }

    #[tokio::test]
    async fn rpc_verify_block_warns_for_mock_backend() {
        let dir = TempDir::new().unwrap();
        let state = make_state(dir.path());
        let block = make_block_with_proof("hash_warn");
        state.store.save_block(&block).unwrap();

        let app = router(state);
        let resp = app
            .oneshot(
                Request::builder()
                    .uri("/verify_block/hash_warn")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let body = resp.into_body().collect().await.unwrap().to_bytes();
        let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert!(json["warning"].as_str().unwrap().contains("not a cryptographic ZK proof"));
    }
}
