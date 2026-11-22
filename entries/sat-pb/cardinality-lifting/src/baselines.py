"""Pigeonhole / mutilated-chessboard benchmark: CDCL vs cutting planes vs CP-SAT,
on clausal (CNF) and native cardinality encodings.

Usage: python3 baselines.py worker <family> <n> <enc> <solver> <timeout>
       python3 baselines.py run <timeout> <out.csv>
"""

import csv
import json
import subprocess
import sys
import time

# ---------- instances: list of clauses (lists of signed ints) and native constraints ----------


def php(n):
    """n+1 pigeons, n holes. var(p,h) = p*n+h+1. Returns (nvars, alo_groups, amo_groups)."""

    def v(p, h):
        return p * n + h + 1

    alo = [[v(p, h) for h in range(n)] for p in range(n + 1)]  # each pigeon somewhere
    amo = [[v(p, h) for p in range(n + 1)] for h in range(n)]  # each hole at most one
    return (n + 1) * n, alo, amo


def mchess(n):
    """n x n board, opposite corners removed, domino = edge between adjacent cells.
    Each remaining cell covered exactly once. Returns (nvars, alo_groups, amo_groups)."""
    removed = {(0, 0), (n - 1, n - 1)}
    cells = [(i, j) for i in range(n) for j in range(n) if (i, j) not in removed]
    idx, inc = {}, {c: [] for c in cells}
    for i, j in cells:
        for a, b in ((i + 1, j), (i, j + 1)):
            if (a, b) in inc:
                e = len(idx) + 1
                idx[((i, j), (a, b))] = e
                inc[(i, j)].append(e)
                inc[(a, b)].append(e)
    groups = [inc[c] for c in cells]
    return len(idx), groups, groups  # exactly-one per cell


FAMILIES = {"php": php, "mchess": mchess}


def to_cnf(nvars, alo, amo, enc):
    clauses = [list(g) for g in alo]
    top = nvars
    for g in amo:
        if enc == "pair":
            clauses += [[-g[i], -g[j]] for i in range(len(g)) for j in range(i + 1, len(g))]
        elif enc == "seq":  # Sinz sequential counter, at-most-one
            k = len(g)
            s = list(range(top + 1, top + k))
            top += k - 1
            clauses.append([-g[0], s[0]])
            for i in range(1, k - 1):
                clauses += [[-g[i], s[i]], [-s[i - 1], s[i]], [-g[i], -s[i - 1]]]
            clauses.append([-g[k - 1], -s[k - 2]])
        else:
            raise ValueError(enc)
    return top, clauses


# ---------- solvers ----------


def run_cadical(nv, cls, timeout):
    import threading

    from pysat.solvers import Solver

    s = Solver(name="cadical195", bootstrap_with=cls)
    t = threading.Timer(timeout, s.interrupt)
    t.start()
    r = s.solve_limited(expect_interrupt=True)
    t.cancel()
    st = s.accum_stats()
    s.delete()
    return {None: "TIMEOUT", False: "UNSAT", True: "SAT"}[r], st.get("conflicts")


def run_exact(nv, cls_or_native, timeout, native=None):
    import exact

    s = exact.Exact()
    for i in range(1, nv + 1):
        s.addVariable(f"x{i}")
    if native is None:
        for c in cls_or_native:  # clause as sum of literals >= 1, with ~x = 1 - x
            terms = [(1 if lit > 0 else -1, f"x{abs(lit)}") for lit in c]
            lb = 1 - sum(1 for lit in c if lit < 0)
            s.addConstraint(terms, True, lb)
    else:
        alo, amo = native
        for g in alo:
            s.addConstraint([(1, f"x{i}") for i in g], True, 1)
        for g in amo:
            s.addConstraint([(1, f"x{i}") for i in g], False, 0, True, 1)
    r = s.runFull(False, timeout)
    stats = s.getStats()
    conf = dict(stats).get("conflicts") if hasattr(stats, "__iter__") else None
    m = {"UNSAT": "UNSAT", "INCONSISTENT": "UNSAT", "SAT": "SAT", "TIMEOUT": "TIMEOUT"}
    return m.get(r, r), conf


def run_cpsat(nv, cls, timeout, native=None, workers=1):
    from ortools.sat.python import cp_model

    md = cp_model.CpModel()
    x = [None] + [md.new_bool_var(f"x{i}") for i in range(1, nv + 1)]

    def to_lit(lit):
        return x[lit] if lit > 0 else x[-lit].Not()

    if native is None:
        for c in cls:
            md.add_bool_or([to_lit(lit) for lit in c])
    else:
        alo, amo = native
        for g in alo:
            md.add_bool_or([x[i] for i in g])
        for g in amo:
            md.add_at_most_one([x[i] for i in g])
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = timeout
    sv.parameters.num_workers = workers
    st = sv.solve(md)
    name = {
        cp_model.INFEASIBLE: "UNSAT",
        cp_model.FEASIBLE: "SAT",
        cp_model.OPTIMAL: "SAT",
        cp_model.UNKNOWN: "TIMEOUT",
    }.get(st, str(st))
    return name, sv.num_conflicts


def worker(fam, n, enc, solver, timeout):
    nv, alo, amo = FAMILIES[fam](n)
    t0 = time.perf_counter()
    if enc == "native":
        nat = (alo, amo)
        if solver == "exact":
            res = run_exact(nv, None, timeout, native=nat)
        elif solver.startswith("cpsat"):
            res = run_cpsat(nv, None, timeout, native=nat, workers=int(solver[5:] or 1))
        else:
            raise ValueError("native encoding needs a PB/CP solver")
        ncl = len(alo) + len(amo)
    else:
        top, cls = to_cnf(nv, alo, amo, enc)
        ncl = len(cls)
        if solver == "cadical":
            res = run_cadical(top, cls, timeout)
        elif solver == "exact":
            res = run_exact(top, cls, timeout)
        elif solver.startswith("cpsat"):
            res = run_cpsat(top, cls, timeout, workers=int(solver[5:] or 1))
        else:
            raise ValueError(solver)
    dt = time.perf_counter() - t0
    print(
        json.dumps(
            {"status": res[0], "conflicts": res[1], "seconds": round(dt, 3), "constraints": ncl}
        )
    )


CONFIGS = [  # (solver, encoding)
    ("cadical", "pair"),
    ("cadical", "seq"),
    ("exact", "pair"),
    ("exact", "seq"),
    ("exact", "native"),
    ("cpsat1", "pair"),
    ("cpsat1", "seq"),
    ("cpsat1", "native"),
]
SIZES = {
    "php": list(range(6, 21)) + [25, 30, 40, 60, 100],
    "mchess": [4, 6, 8, 10, 12, 14, 16, 20, 24, 30, 40],
}


def run_all(timeout, out):
    rows = []
    for fam, sizes in SIZES.items():
        for solver, enc in CONFIGS:
            for n in sizes:
                cmd = [sys.executable, __file__, "worker", fam, str(n), enc, solver, str(timeout)]
                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
                    line = [lit for lit in p.stdout.splitlines() if lit.startswith("{")]
                    r = json.loads(line[-1]) if line else {"status": "ERROR:" + p.stderr[-200:]}
                except subprocess.TimeoutExpired:
                    r = {"status": "TIMEOUT", "seconds": timeout}
                row = {"family": fam, "n": n, "solver": solver, "encoding": enc, **r}
                rows.append(row)
                print(row, flush=True)
                if r["status"] != "UNSAT":
                    break  # stop escalating this config after first timeout/error
    keys = ["family", "n", "solver", "encoding", "status", "seconds", "conflicts", "constraints"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], float(sys.argv[6]))
    else:
        run_all(float(sys.argv[2]), sys.argv[3])
