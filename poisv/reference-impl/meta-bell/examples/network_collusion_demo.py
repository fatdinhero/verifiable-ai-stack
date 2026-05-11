"""Gradually increase collusion fraction and plot the Psi drop."""
import numpy as np

from meta_bell.src.meta_bell import meta_bell_psi

def main() -> int:
    rng = np.random.default_rng(0)
    N, k = 10, 64
    for q in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        n_col = int(round(q * N))
        shared = rng.uniform(0, 0.5, k).tolist()
        rows = ([shared] * n_col +
                [rng.uniform(0, 0.5, k).tolist() for _ in range(N - n_col)])
        psi = meta_bell_psi(rows)
        print(f'q={q:.1f}  Psi={psi:.3f}  (N={N}, k={k})')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
