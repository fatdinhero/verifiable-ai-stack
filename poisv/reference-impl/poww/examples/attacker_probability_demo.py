from agentsprotocol.wise_score import attacker_probability_table

def main() -> int:
    print(f'{"q":>6} {"z":>4} {"P(catchup)":>16}')
    for q, z, p in attacker_probability_table():
        print(f'{q:>6.2f} {z:>4d} {p:>16.3e}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
