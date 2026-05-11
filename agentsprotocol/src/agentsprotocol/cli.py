"""Command-line interface: `agentsprotocol <command>`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from . import __doi__, __version__
from .psi_test import attacker_success_bound, compute_psi, compute_psi_weighted
from .s_con import compute_s_con
from .schemas import Claim
from .wise_score import compute_wise_score_aggregate


def _cmd_validate(args: argparse.Namespace) -> int:
    claim_path = Path(args.claim)
    if not claim_path.exists():
        print(f"error: {claim_path} not found", file=sys.stderr)
        return 2
    data = json.loads(claim_path.read_text(encoding="utf-8"))
    try:
        claim = Claim.model_validate(data)
    except Exception as exc:
        print(f"schema error: {exc}", file=sys.stderr)
        return 1
    corpus = list(args.fact) if args.fact else []
    score = compute_s_con(claim.payload.statement, corpus, tau=args.tau)
    print(json.dumps({"claim_id": claim.id, "s_con": score, "tau": args.tau}, indent=2))
    return 0


def _cmd_psi(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.errors).read_text(encoding="utf-8"))
    errors = data.get("error_vectors") or data
    stakes = data.get("stakes") if isinstance(data, dict) else None
    if stakes:
        psi = compute_psi_weighted(errors, stakes)
    else:
        psi = compute_psi(errors)
    print(json.dumps({"psi": psi, "weighted": bool(stakes)}, indent=2))
    return 0


def _cmd_wise(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.units).read_text(encoding="utf-8"))
    agg = compute_wise_score_aggregate(
        data["v"], data["c"], data["r"], data["e"], alpha=args.alpha,
    )
    print(json.dumps({"poww_aggregate": agg, "n": len(data["v"])}, indent=2))
    return 0


def _cmd_bound(args: argparse.Namespace) -> int:
    p = attacker_success_bound(args.q, args.k, psi_min=args.psi_min)
    print(json.dumps({
        "q": args.q, "k": args.k, "psi_min": args.psi_min, "P_success_upper_bound": p,
    }, indent=2))
    return 0


def _cmd_info(_: argparse.Namespace) -> int:
    print(f"agentsprotocol {__version__}")
    print(f"DOI: {__doi__}")
    print("Author: Fatih Dinc <fatdinhero@gmail.com>")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentsprotocol",
                                     description="AgentsProtocol reference CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="compute S_con for a claim.json")
    v.add_argument("claim")
    v.add_argument("--fact", action="append",
                   help="corpus fact string (repeat for multiple)")
    v.add_argument("--tau", type=float, default=0.7)
    v.set_defaults(func=_cmd_validate)

    p = sub.add_parser("psi", help="compute Psi from error_vectors.json")
    p.add_argument("errors")
    p.set_defaults(func=_cmd_psi)

    w = sub.add_parser("wise", help="compute aggregate WiseScore from units.json")
    w.add_argument("units")
    w.add_argument("--alpha", type=float, default=1.0)
    w.set_defaults(func=_cmd_wise)

    b = sub.add_parser("bound", help="Hoeffding attacker-success upper bound")
    b.add_argument("--q", type=float, required=True, help="attacker fraction")
    b.add_argument("--k", type=int, required=True, help="control-set size")
    b.add_argument("--psi-min", type=float, default=0.7)
    b.set_defaults(func=_cmd_bound)

    i = sub.add_parser("info", help="print protocol version / DOI")
    i.set_defaults(func=_cmd_info)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
