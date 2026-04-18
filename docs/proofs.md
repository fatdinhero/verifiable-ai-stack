# Theorem Summaries

Extracted from the three whitepapers in the archive (see `README.md`).

## Meta-Bell Theory (arXiv-style §1-4)

- **Theorem 1.1** (Existence and Uniqueness of Classical Expected Values).
  Under measurability, normalisability, and perturbation invariance, the
  classical expected value exists uniquely and is continuous in the
  hidden-variable parameter.
- **Theorem 1.2** (Properties of the Entanglement Measure). Psi(X,Y) >= 0;
  Psi(X,Y) = 0 iff the system is classically explainable; Psi > 0 signals
  a Meta-Bell violation; Psi is continuous in the perturbation parameters.
- **Theorem 2.1/2.2/2.3** (Dynamics). The Meta-Bell ODE with logistic
  growth, impulsive forcing, and noise has a unique solution on every
  finite interval. Equilibria at Psi*=0 (unstable) and Psi*=1/beta
  (asymptotically stable) for alpha > 0.
- **Theorem 2.4** (Transcritical Bifurcation). At alpha = 0 stability of
  the two equilibria exchanges.
- **Theorem 3.1** (Embedding of CHSH). With trivial perturbation D = Id
  and local hidden variables, the Meta-Bell inequality reduces to the
  classical CHSH inequality bounded by 2.
- **Theorem 4.1/4.2** (Statistical Inference). The Meta-Bell test
  statistic T_n is asymptotically normal under H0:Psi=0; test power is
  Phi(sqrt(n) Psi_1 / sigma - z_{1-alpha}).

## Proof of WiseWork v2

- **Lemma 1** (Two-validator CHSH reduction). In the special case of two
  validators with two binary measurement settings each, Psi reduces to
  the normalised deviation of the classical CHSH quantity from the bound
  of two.
- **Gambler's Ruin probability**. For honest/attacker next-block
  probabilities p, q with p > q and an initial deficit z blocks,
  P(catch-up) = (q/p)^z.

## PoISV v1.0

- **Attacker-success upper bound (§5.2).** Hoeffding's inequality for
  U-statistics applied to the Psi statistic gives an exponential bound
  in k (see math.md).
- **Incentive compatibility (§5.3).** Manipulation requires genuinely
  independent pipelines, defeating the coordination purpose.
