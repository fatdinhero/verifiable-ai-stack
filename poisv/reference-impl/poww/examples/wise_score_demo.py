from agentsprotocol.wise_score import compute_wise_score, compute_wise_score_aggregate

def main() -> int:
    v = [0.9, 0.8, 0.95, 0.6]   # truth candidates
    c = [1.0, 2.0, 1.5, 0.8]   # context weights
    r = [5.0, 2.0, 4.0, 6.0]   # relevance
    e = [1.0, 0.9, 0.8, 0.3]   # ethical compliance
    w = compute_wise_score(v, c, r, e)
    print('W(i) =', [round(x, 4) for x in w])
    print('PoWW =', round(compute_wise_score_aggregate(v, c, r, e), 4))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
