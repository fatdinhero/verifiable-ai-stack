from agentsprotocol.s_con import compute_s_con
from agentsprotocol.psi_test import compute_psi, check_acceptance
from agentsprotocol.validator import block_weight

def main() -> int:
    claim_texts = ['The sky is blue.', 'Water is wet.']
    corpus = ['The sky is blue.', 'Water is wet.']
    s_cons = [compute_s_con(c, corpus, tau=0.7) for c in claim_texts]
    # synthesise 3 validator error vectors on a 5-task control set
    ev = [[0.1, 0.2, 0.15, 0.05, 0.3],
          [0.3, 0.1, 0.05, 0.2, 0.15],
          [0.2, 0.3, 0.1, 0.15, 0.05]]
    psi = compute_psi(ev)
    ok = check_acceptance(s_cons, psi, theta_min=0.6, psi_min=0.3)
    print(f'mean S_con = {sum(s_cons)/len(s_cons):.3f}  Psi = {psi:.3f}')
    print(f'accepted = {ok}  weight = {block_weight(psi, s_cons):.3f}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
