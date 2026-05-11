//! S_con + Psi — Rust implementation.
//!
//! Mirrors the Python reference in `src/agentsprotocol/s_con.py` and
//! `src/agentsprotocol/psi_test.py` exactly. See DevDocs §3 and §4.2.
//! DOI: 10.5281/zenodo.19642292
//!
//! Formula:
//!   S_con(A) = max(0, (cos(v_A, mean(v_kappa)) - tau) / (1 - tau))
//!
//!   Psi   = 1 - (2 / N(N-1)) * sum_{i<j} |rho(e_i, e_j)|
//!   Psi_w = 1 - sum_{i<j} w_i w_j |rho| / sum_{i<j} w_i w_j,  w_i = sqrt(s_i)

use sha2::{Digest, Sha256};

use crate::config::ProtocolConfig;

// -- Vector helpers -----------------------------------------------------------

/// Cosine similarity of two vectors. Returns 0.0 if either is the zero vector.
pub fn cosine_similarity(a: &[f64], b: &[f64]) -> f64 {
    debug_assert_eq!(a.len(), b.len(), "cosine_similarity: dimension mismatch");
    let dot: f64 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let nb: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    if na == 0.0 || nb == 0.0 {
        return 0.0;
    }
    (dot / (na * nb)).clamp(-1.0, 1.0)
}

/// Element-wise mean of a slice of equal-length vectors.
fn mean_vector(vecs: &[Vec<f64>]) -> Vec<f64> {
    if vecs.is_empty() {
        return Vec::new();
    }
    let dim = vecs[0].len();
    let n = vecs.len() as f64;
    let mut out = vec![0.0f64; dim];
    for v in vecs {
        for (acc, x) in out.iter_mut().zip(v) {
            *acc += x;
        }
    }
    out.iter_mut().for_each(|x| *x /= n);
    out
}

// -- Deterministic stub embedder ----------------------------------------------

/// Deterministic 384-dim embedding derived from SHA-256, matching the Python
/// `_stub_embed`. Used for tests; production nodes use an ONNX embedder.
///
/// Algorithm (mirrors Python exactly):
///   1. SHA-256(text) -> 32 bytes
///   2. Tile to 384 bytes, cast to f64, subtract 127.5
///   3. L2-normalise
pub fn stub_embed(text: &str) -> Vec<f64> {
    const DIM: usize = 384;
    let hash = Sha256::digest(text.as_bytes());
    let mut raw = vec![0u8; DIM];
    for (i, b) in raw.iter_mut().enumerate() {
        *b = hash[i % 32];
    }
    let mut vec: Vec<f64> = raw.iter().map(|&b| b as f64 - 127.5).collect();
    let norm: f64 = vec.iter().map(|x| x * x).sum::<f64>().sqrt();
    if norm > 0.0 {
        vec.iter_mut().for_each(|x| *x /= norm);
    }
    vec
}

// -- S_con --------------------------------------------------------------------

/// Compute S_con from pre-embedded vectors (DevDocs §3).
///
/// `claim_vec`   -- embedding of the claim statement.
/// `corpus_vecs` -- embeddings of the retrieved corpus facts.
/// `tau`         -- acceptance threshold in [0, 1).
pub fn s_con_from_vecs(claim_vec: &[f64], corpus_vecs: &[Vec<f64>], tau: f64) -> f64 {
    assert!(
        (0.0..1.0).contains(&tau),
        "tau must be in [0, 1), got {tau}"
    );
    if corpus_vecs.is_empty() {
        return 0.0;
    }
    let v_mean = mean_vector(corpus_vecs);
    let cos = cosine_similarity(claim_vec, &v_mean);
    f64::max(0.0, (cos - tau) / (1.0 - tau))
}

/// Embed claim + corpus with `embed_fn`, then compute S_con.
/// Mirrors `compute_s_con` in the Python reference.
pub fn compute_s_con<F>(claim_text: &str, corpus: &[&str], embed_fn: F, tau: f64) -> f64
where
    F: Fn(&str) -> Vec<f64>,
{
    if corpus.is_empty() {
        return 0.0;
    }
    let claim_vec = embed_fn(claim_text);
    let corpus_vecs: Vec<Vec<f64>> = corpus.iter().map(|s| embed_fn(s)).collect();
    s_con_from_vecs(&claim_vec, &corpus_vecs, tau)
}

// -- Pearson correlation ------------------------------------------------------

/// Pearson r of two equal-length slices.
/// Returns 0.0 for constant vectors (std = 0) -- same convention as Python.
fn pearson_r(x: &[f64], y: &[f64]) -> f64 {
    let n = x.len() as f64;
    if n < 2.0 {
        return 0.0;
    }
    let mx = x.iter().sum::<f64>() / n;
    let my = y.iter().sum::<f64>() / n;
    let cov: f64 = x.iter().zip(y).map(|(xi, yi)| (xi - mx) * (yi - my)).sum();
    let sx: f64 = x.iter().map(|xi| (xi - mx).powi(2)).sum::<f64>().sqrt();
    let sy: f64 = y.iter().map(|yi| (yi - my).powi(2)).sum::<f64>().sqrt();
    if sx == 0.0 || sy == 0.0 {
        return 0.0;
    }
    (cov / (sx * sy)).clamp(-1.0, 1.0)
}

// -- Error vectors ------------------------------------------------------------

/// e_i[j] = |S_i(D_j) - S*(D_j)|  (DevDocs §4.1)
pub fn compute_error_vectors(
    validator_scores: &[Vec<f64>],
    reference_scores: &[f64],
) -> Vec<Vec<f64>> {
    validator_scores
        .iter()
        .map(|row| {
            assert_eq!(
                row.len(),
                reference_scores.len(),
                "validator row length mismatch"
            );
            row.iter()
                .zip(reference_scores)
                .map(|(s, r)| (s - r).abs())
                .collect()
        })
        .collect()
}

// -- Psi ----------------------------------------------------------------------

/// Unweighted Psi (PoISV §3.3).
///
/// Psi = 1 - (2 / N(N-1)) * sum_{i<j} |rho(e_i, e_j)|
pub fn compute_psi(error_vectors: &[Vec<f64>]) -> f64 {
    let n = error_vectors.len();
    if n < 2 {
        return 1.0;
    }
    let num_pairs = (n * (n - 1)) / 2;
    let mut corr_sum = 0.0f64;
    for i in 0..n {
        for j in (i + 1)..n {
            corr_sum += pearson_r(&error_vectors[i], &error_vectors[j]).abs();
        }
    }
    let mean_abs_corr = corr_sum / num_pairs as f64;
    (1.0 - mean_abs_corr).clamp(0.0, 1.0)
}

/// Stake-weighted Psi with w_i = sqrt(s_i) (DevDocs §4.2).
///
/// Psi_w = 1 - sum_{i<j} w_i w_j |rho| / sum_{i<j} w_i w_j
pub fn compute_psi_weighted(error_vectors: &[Vec<f64>], stakes: &[f64]) -> f64 {
    let n = error_vectors.len();
    assert_eq!(stakes.len(), n, "stakes length must match validator count");
    if n < 2 {
        return 1.0;
    }
    let weights: Vec<f64> = stakes.iter().map(|&s| s.max(0.0).sqrt()).collect();
    let mut corr_sum = 0.0f64;
    let mut w_sum = 0.0f64;
    for i in 0..n {
        for j in (i + 1)..n {
            let w = weights[i] * weights[j];
            corr_sum += w * pearson_r(&error_vectors[i], &error_vectors[j]).abs();
            w_sum += w;
        }
    }
    if w_sum == 0.0 {
        return 0.0;
    }
    (1.0 - corr_sum / w_sum).clamp(0.0, 1.0)
}

// -- Validator struct ---------------------------------------------------------

pub struct Validator {
    pub cfg: ProtocolConfig,
}

impl Validator {
    pub fn new(cfg: ProtocolConfig) -> Self {
        Self { cfg }
    }

    /// S_con(A) using the stub embedder. See DevDocs §3.
    pub fn s_con(&self, claim_text: &str, corpus: &[String]) -> f64 {
        let corpus_refs: Vec<&str> = corpus.iter().map(String::as_str).collect();
        compute_s_con(claim_text, &corpus_refs, stub_embed, self.cfg.tau)
    }

    /// Unweighted Psi. See DevDocs §4.2.
    pub fn psi(&self, error_vectors: &[Vec<f64>]) -> f64 {
        compute_psi(error_vectors)
    }

    /// Stake-weighted Psi with w_i = sqrt(s_i). See DevDocs §4.2.
    pub fn psi_weighted(&self, error_vectors: &[Vec<f64>], stakes: &[f64]) -> f64 {
        compute_psi_weighted(error_vectors, stakes)
    }
}

// -- Tests --------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cosine_identical() {
        let v = vec![1.0, 2.0, 3.0];
        assert!((cosine_similarity(&v, &v) - 1.0).abs() < 1e-10);
    }

    #[test]
    fn cosine_orthogonal() {
        assert!(cosine_similarity(&[1.0, 0.0], &[0.0, 1.0]).abs() < 1e-10);
    }

    #[test]
    fn cosine_zero_vector() {
        assert_eq!(cosine_similarity(&[0.0, 0.0], &[1.0, 2.0]), 0.0);
    }

    #[test]
    fn stub_embed_deterministic() {
        assert_eq!(stub_embed("hello"), stub_embed("hello"));
    }

    #[test]
    fn stub_embed_different_inputs_differ() {
        assert_ne!(stub_embed("a"), stub_embed("b"));
    }

    #[test]
    fn stub_embed_is_unit_vector() {
        let v = stub_embed("test");
        let norm: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        assert!((norm - 1.0).abs() < 1e-10);
    }

    #[test]
    fn stub_embed_dim() {
        assert_eq!(stub_embed("x").len(), 384);
    }

    #[test]
    fn s_con_empty_corpus_is_zero() {
        assert_eq!(compute_s_con("claim", &[], stub_embed, 0.7), 0.0);
    }

    #[test]
    fn s_con_identical_text_is_one() {
        let txt = "The sky is blue.";
        let score = compute_s_con(txt, &[txt], stub_embed, 0.7);
        assert!((score - 1.0).abs() < 1e-10, "got {score}");
    }

    #[test]
    fn s_con_range_bounded() {
        for tau in [0.0, 0.3, 0.7, 0.99] {
            let s = compute_s_con("claim", &["claim", "other"], stub_embed, tau);
            assert!((0.0..=1.0).contains(&s), "tau={tau} s={s}");
        }
    }

    #[test]
    fn psi_single_validator_is_one() {
        assert_eq!(compute_psi(&[vec![0.1, 0.2, 0.3]]), 1.0);
    }

    #[test]
    fn psi_empty_is_one() {
        assert_eq!(compute_psi(&[]), 1.0);
    }

    #[test]
    fn psi_identical_validators_is_zero() {
        let e = vec![vec![0.1, 0.2, 0.3, 0.4], vec![0.1, 0.2, 0.3, 0.4]];
        assert!(compute_psi(&e) < 1e-9, "expected ~0, got {}", compute_psi(&e));
    }

    #[test]
    fn psi_anticorrelated_is_zero() {
        let e = vec![vec![0.1, 0.2, 0.3, 0.4], vec![0.4, 0.3, 0.2, 0.1]];
        assert!(compute_psi(&e) < 1e-9);
    }

    #[test]
    fn psi_constant_vectors_treated_as_independent() {
        // std=0 -> pearson_r=0 -> Psi=1
        let e = vec![vec![0.5; 5], vec![0.2; 5]];
        assert!((compute_psi(&e) - 1.0).abs() < 1e-10);
    }

    #[test]
    fn psi_weighted_equal_stakes_matches_unweighted() {
        let errors = vec![
            vec![0.1, 0.3, 0.2],
            vec![0.2, 0.1, 0.4],
            vec![0.4, 0.2, 0.3],
        ];
        let psi_uw = compute_psi(&errors);
        let psi_w = compute_psi_weighted(&errors, &[1.0, 1.0, 1.0]);
        assert!((psi_uw - psi_w).abs() < 1e-9, "uw={psi_uw} w={psi_w}");
    }

    #[test]
    fn psi_weighted_zero_stakes_is_zero() {
        let e = vec![vec![0.1, 0.2], vec![0.2, 0.1]];
        assert_eq!(compute_psi_weighted(&e, &[0.0, 0.0]), 0.0);
    }

    #[test]
    fn error_vectors_values() {
        let scores = vec![vec![0.9, 0.8, 1.0], vec![0.7, 0.95, 0.88]];
        let refs = vec![1.0, 0.9, 0.95];
        let ev = compute_error_vectors(&scores, &refs);
        assert!((ev[0][0] - 0.1).abs() < 1e-10);
        assert!((ev[0][1] - 0.1).abs() < 1e-10);
        assert!((ev[0][2] - 0.05).abs() < 1e-10);
        assert!((ev[1][0] - 0.3).abs() < 1e-10);
    }

    #[test]
    fn validator_s_con_same_text_is_one() {
        let cfg = crate::config::ProtocolConfig::load().unwrap();
        let v = Validator::new(cfg);
        let corpus = vec!["The sky is blue.".to_string()];
        let score = v.s_con("The sky is blue.", &corpus);
        assert!((score - 1.0).abs() < 1e-10, "got {score}");
    }
}
