"""This entry as a candidate for the problem card's evaluator: rewrite, then Exact.

Called as `python candidate.py <file.cnf>`; prints `s UNSATISFIABLE` or `s SATISFIABLE`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cardlift  # noqa: E402

if __name__ == "__main__":
    nv, clauses = cardlift.read_dimacs(sys.argv[1])
    top, rewritten, amos = cardlift.lift(nv, clauses, {})
    status, _, model = cardlift.solve_exact(top, rewritten, amos, 3600)
    if status == "SAT" and not cardlift.check_model(clauses, model):
        print("s UNKNOWN")
    else:
        print({"SAT": "s SATISFIABLE", "UNSAT": "s UNSATISFIABLE"}.get(status, "s UNKNOWN"))
