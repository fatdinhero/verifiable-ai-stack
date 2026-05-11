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
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tracing::{info, warn};

use crate::mempool::ClaimMempool;
use crate::storage::{DagStore, StoredClaim};
use crate::validation::verify_claim_signature;

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
