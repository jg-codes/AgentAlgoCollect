"""Produce a certificate (definitions, lifted constraints, Farkas multipliers) for a CNF.

Usage: python3 certify.py <cnf> <cert.json>
The certificate claims the lifted constraint system is infeasible even over [0,1]^n.
"""

import json
import sys
import time
from fractions import Fraction

import cardlift
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


def lifted_system(top, clauses, amos):
    """Rows as (coeffs dict var->int, rhs) meaning sum coeffs*x >= rhs."""
    rows = []
    for c in clauses:  # sum lits >= 1, ~x = 1-x
        co, rhs = {}, 1
        for lit in c:
            if lit > 0:
                co[lit] = co.get(lit, 0) + 1
            else:
                co[-lit] = co.get(-lit, 0) - 1
                rhs -= 1
        rows.append((co, rhs))
    for g in amos:  # sum lits <= 1  ->  -sum lits >= -1
        co, rhs = {}, -1
        for lit in g:
            if lit > 0:
                co[lit] = co.get(lit, 0) - 1
            else:
                co[-lit] = co.get(-lit, 0) + 1
                rhs += 1
        rows.append((co, rhs))
    return rows


def farkas(top, rows):
    m = len(rows)
    # phase-1 LP: min sum s  s.t. A x + s >= b, 0<=x<=1, s>=0 ;  x indices 0..top-1, s top..top+m-1
    A = lil_matrix((m, top + m))
    b = np.zeros(m)
    for i, (co, rhs) in enumerate(rows):
        for v, a in co.items():
            A[i, v - 1] = -a
        A[i, top + i] = -1.0
        b[i] = -rhs
    c = np.concatenate([np.zeros(top), np.ones(m)])
    bounds = [(0, 1)] * top + [(0, None)] * m
    res = linprog(c, A_ub=A.tocsr(), b_ub=b, bounds=bounds, method="highs")
    if res.status != 0 or res.fun <= 1e-7:
        return None, res.fun
    y = -res.ineqlin.marginals  # duals >= 0 of the >= rows
    ys = {}
    for i, v in enumerate(y):
        if v > 1e-9:
            ys[i] = Fraction(v).limit_denominator(10**6)
    return ys, res.fun


if __name__ == "__main__":
    path, out = sys.argv[1], sys.argv[2]
    t0 = time.perf_counter()
    nv, cls = cardlift.read_dimacs(path)
    st = {}
    top, c2, amos = cardlift.lift(nv, cls, st)
    rows = lifted_system(top, c2, amos)
    ys, phase1 = farkas(top, rows)
    cert = {
        "nv": nv,
        "top": top,
        "defs": st.get("_defs", []),
        "clauses": c2,
        "amos": amos,
        "farkas": None
        if ys is None
        else {str(i): [f.numerator, f.denominator] for i, f in ys.items()},
        "phase1_obj": phase1,
    }
    json.dump(cert, open(out, "w"))
    print(
        json.dumps(
            {
                "file": path,
                "lp_infeasible": ys is not None,
                "phase1_obj": phase1,
                "nonzero_multipliers": 0 if ys is None else len(ys),
                "seconds": round(time.perf_counter() - t0, 2),
            }
        )
    )
