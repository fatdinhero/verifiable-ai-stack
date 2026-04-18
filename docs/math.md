# Mathematical Foundations

All formulas below come from the whitepaper archive at
DOI 10.5281/zenodo.19642292.

## Semantic Consistency Score (DevDocs §3)

$$S_{\text{con}}(A) = \max\!\left(0,\ \frac{\cos(v_A,\ \bar v_\kappa) - \tau}{1 - \tau}\right),\quad \tau \in [0, 1).$$

## Non-Collusion Statistic (PoISV §3.3, unweighted)

$$\Psi = 1 - \frac{2}{N(N-1)} \sum_{1 \le i < j \le N} |\rho(e_i, e_j)|.$$

## Weighted form (DevDocs §4.2, $w_i = \sqrt{s_i}$)

$$\Psi = 1 - \frac{\sum_{i<j} w_i w_j |\rho(e_i, e_j)|}{\sum_{i<j} w_i w_j}.$$

## Acceptance Rule (DevDocs §8 / PoISV §3.4)

$$\frac{1}{|B|} \sum_{A \in B} S_{\text{con}}(A) \ge \theta_{\min} \quad \land \quad \Psi_B \ge \Psi_{\min} \quad \land \quad \pi_B \text{ verifies}.$$

Defaults: $\theta_{\min} = 0.6$, $\Psi_{\min} = 0.7$.

## Block Weight (DevDocs §5.2 / PoISV §3.5)

$$W(B) = \Psi_B \cdot \sum_{A \in B} S_{\text{con}}(A).$$

## Attacker-success Upper Bound (PoISV §5.2)

$$P(\text{Success}) \le \exp\!\left(-2k \cdot \frac{(1-q)^2}{q^2} \cdot \frac{\Psi_{\min} - (1 - q^2)}{2}\right).$$

The bound is non-trivial precisely when $\Psi_{\min} > 1 - q^2$.

## WiseScore (PoWW v2 §4)

$$T(i) = \frac{\exp(\alpha v_i)}{\sum_j \exp(\alpha v_j)},\quad C(i) = \frac{c_i}{\sum_j c_j},\quad R(i) = \log(1 + r_i),\quad E(i) = e_i.$$

$$W(i) = T(i) \cdot C(i) \cdot R(i) \cdot E(i),\quad \text{PoWW} = \frac{1}{|I|} \sum_{i \in I} W(i).$$

## Attacker Catch-up Probability (PoWW v2 §11, Gambler's Ruin)

$$P_{\text{catchup}}(q, z) = 1 - \sum_{k=0}^{z} \operatorname{Poisson}(k; z q/p) \cdot \left(1 - (q/p)^{z-k}\right),\quad p = 1 - q.$$
