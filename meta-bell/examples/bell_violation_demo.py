"""Contrast independent vs colluding validators on a control set."""
import numpy as np

from meta_bell.src.meta_bell import meta_bell_psi

def main() -> int:
    rng = np.random.default_rng(42)
    k = 64
    independent = [rng.uniform(0, 0.5, k).tolist() for _ in range(6)]
    colluding = [independent[0]] * 6  # identical errors
    print(f'Psi(independent) = {meta_bell_psi(independent):.4f}')
    print(f'Psi(colluding)   = {meta_bell_psi(colluding):.4f}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
