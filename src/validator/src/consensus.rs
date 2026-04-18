//! GHOSTDAG consensus — skeleton.
//!
//! Reference: Sompolinsky, Wyborski, Zohar, AFT 2021.
//! Block weight: Weight(B) = Psi_B * sum_A S_con(A) (PoISV 3.5 / DevDocs 5.2).

use crate::config::ProtocolConfig;
use crate::storage::DagStore;

pub struct Ghostdag<'a> { pub cfg: ProtocolConfig, pub _store: &'a DagStore }

impl<'a> Ghostdag<'a> {
    pub fn new(cfg: ProtocolConfig, store: &'a DagStore) -> Self { Self { cfg, _store: store } }

    /// Weight(B) = Psi_B * sum_A S_con(A)
    pub fn block_weight(&self, psi: f64, s_cons: &[f64]) -> f64 {
        psi * s_cons.iter().sum::<f64>()
    }
}
