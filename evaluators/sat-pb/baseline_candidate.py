"""Baseline candidate for the evaluator: a clause-learning SAT solver without any rewrite.

Needs `pip install python-sat`. A starting point for people and for automated code search.
"""

from __future__ import annotations

import sys

from pysat.formula import CNF
from pysat.solvers import Solver

if __name__ == "__main__":
    with Solver(name="cadical195", bootstrap_with=CNF(from_file=sys.argv[1]).clauses) as solver:
        print("s SATISFIABLE" if solver.solve() else "s UNSATISFIABLE")
