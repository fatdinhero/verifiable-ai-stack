"""Minimal Kaspa demo using the simulation mode."""
from agentsprotocol.kaspa import GhostdagBridge, simulate_dag
from agentsprotocol.psi_test import compute_psi

def main() -> int:
    blocks = simulate_dag(num_blocks=5, seed=7)
    bridge = GhostdagBridge()
    for i, b in enumerate(blocks):
        # Example: synthesise validator error vectors per block
        ev = [[0.1, 0.2, 0.15, 0.3], [0.2, 0.1, 0.2, 0.25]]
        psi = compute_psi(ev)
        bridge.annotate(b.block_hash, psi,
                        [0.8 - 0.1 * i, 0.7, 0.75])
    path = bridge.canonical_path([b.block_hash for b in blocks])
    print(f'canonical path ({len(path)} blocks), '
          f'total weight = {bridge.total_weight():.3f}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
