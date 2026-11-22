"""General clause-to-cardinality lifting pre-pass (encoding-agnostic, polarity-agnostic).

Three equivalence-preserving rules, applied to any CNF:
  R1 product extension: a 4-clause (a|b|c|d) whose literals split into two pairs that each
     recur in >= MIN_FREQ 4-clauses is rewritten as (~t1|~t2) with t1 := ~a & ~b, t2 := ~c & ~d
     (full definitions added, i.e. extended resolution).
  R2 substitution: in a clause containing ~x and y where t := x & y is defined, y is replaced by t.
  R3 literal cliques: binary clauses (a|b) are edges (~a,~b) of a literal conflict graph; a greedy
     maximal-clique cover turns them into at-most-one constraints over literals, and the covered
     binary clauses are deleted. Cliques may contain negated literals, so an AMO plus a shared
     implication is recovered as  sum(C) <= lit  automatically.
No rule looks at variable names, encoding order or the problem family.
"""

from __future__ import annotations

import lzma
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations

MIN_FREQ = 2


def read_dimacs(path: str):
    op = lzma.open if path.endswith(".xz") else open
    nv, cls = 0, []
    with op(path, "rt") as f:
        cur = []
        for line in f:
            if not line or line[0] in "cp%":
                if line.startswith("p"):
                    nv = int(line.split()[2])
                continue
            for tok in line.split():
                v = int(tok)
                if v == 0:
                    cls.append(cur)
                    cur = []
                else:
                    cur.append(v)
    return nv, cls


def lift(nv: int, clauses: list[list[int]], stats: dict | None = None, rules: str = "123"):
    st = stats if stats is not None else {}
    top = nv
    conj: dict[tuple[int, int], int] = {}  # (x, y) -> t  with t := x & y
    defs: list[list[int]] = []

    def get_t(x: int, y: int) -> int:
        nonlocal top
        key = (x, y) if x < y else (y, x)
        t = conj.get(key)
        if t is None:
            top += 1
            t = top
            conj[(x, y)] = conj[(y, x)] = t
            defs.extend([[-t, x], [-t, y], [t, -x, -y]])
            st.setdefault("_defs", []).append((t, x, y))
        return t

    # ---- R1: product extension on 4-clauses
    four_idx = [
        i
        for i, c in enumerate(clauses)
        if "1" in rules and len(c) == 4 and len(set(map(abs, c))) == 4
    ]
    pf = Counter()
    for i in four_idx:
        c = clauses[i]
        for a, b in combinations(sorted(c), 2):
            pf[(a, b)] += 1
    out = []
    n_r1 = 0
    four_set = set(four_idx)
    for i, c in enumerate(clauses):
        if i in four_set:
            a, b, cc, d = sorted(c)
            best, bestv = None, MIN_FREQ - 1
            for p1, p2 in (((a, b), (cc, d)), ((a, cc), (b, d)), ((a, d), (b, cc))):
                v = min(pf[p1], pf[p2])
                if v > bestv:
                    best, bestv = (p1, p2), v
            if best is not None:
                (l1, l2), (l3, l4) = best
                t1, t2 = get_t(-l1, -l2), get_t(-l3, -l4)  # clause pair (l1|l2) == ~t1
                out.append([-t1, -t2])
                n_r1 += 1
                continue
        out.append(list(c))
    st["R1_rewritten_4clauses"] = n_r1
    st["extension_vars"] = top - nv

    # ---- R2: substitution y -> t in clauses containing ~x and y, t := x & y
    n_r2 = 0
    if conj and "2" in rules:
        partners = defaultdict(set)  # x -> {y : (x,y) defined}
        for x, y in conj:
            partners[x].add(y)
        for c in out:
            if len(c) < 3:
                continue
            lits = set(c)
            changed = False
            for lit in list(c):
                if lit not in lits:
                    continue
                x = -lit  # clause contains ~x
                if x not in partners:
                    continue
                for y in partners[x] & lits:
                    t = conj[(x, y)]
                    lits.discard(y)
                    lits.add(t)
                    changed = True
                    n_r2 += 1
            if changed:
                c[:] = sorted(lits)
    st["R2_substitutions"] = n_r2
    out.extend(defs)

    # ---- R3: literal-clique cover of binary clauses
    adj = defaultdict(set)
    rest = []
    for c in out:
        if "3" in rules and len(c) == 2 and abs(c[0]) != abs(c[1]):
            a, b = -c[0], -c[1]
            adj[a].add(b)
            adj[b].add(a)
        else:
            rest.append(c)
    uncovered = {(a, b) for a in adj for b in adj[a] if a < b}
    amos, kept_bin = [], []
    deg = {v: len(s) for v, s in adj.items()}
    for a, b in sorted(uncovered):
        if (a, b) not in uncovered:
            continue
        clique = [a, b]
        for v in sorted(adj[a] & adj[b], key=lambda v: (-deg[v], v)):
            if all(v in adj[u] for u in clique):
                clique.append(v)
        for u, w in combinations(clique, 2):
            uncovered.discard((u, w) if u < w else (w, u))
        if len(clique) >= 3:
            amos.append(clique)
        else:
            kept_bin.append([-a, -b])
    st["R3_amo"] = len(amos)
    st["R3_max_amo"] = max((len(g) for g in amos), default=0)
    st["clauses_out"] = len(rest) + len(kept_bin)
    return top, rest + kept_bin, amos


# ---------------- solvers ----------------


def solve_exact(top, clauses, amos, timeout, proof=None):
    import exact

    opts = [("proof-log", proof)] if proof else []
    s = exact.Exact(opts)
    for i in range(1, top + 1):
        s.addVariable(f"x{i}")

    def terms(lits):
        return [(1 if lit > 0 else -1, f"x{abs(lit)}") for lit in lits], sum(
            1 for lit in lits if lit < 0
        )

    for c in clauses:
        tm, neg = terms(c)
        s.addConstraint(tm, True, 1 - neg)
    for g in amos:
        tm, neg = terms(g)
        s.addConstraint(tm, False, 0, True, 1 - neg)
    r = s.runFull(False, timeout)
    model = None
    if r == "SAT":
        vals = s.getLastSolutionFor([f"x{i}" for i in range(1, top + 1)])
        model = [i if v else -i for i, v in zip(range(1, top + 1), vals, strict=True)]
    return r, dict(s.getStats()).get("conflicts"), model


def solve_cpsat(top, clauses, amos, timeout, workers=1, lin=2):
    from ortools.sat.python import cp_model

    md = cp_model.CpModel()
    x = [None] + [md.new_bool_var(f"x{i}") for i in range(1, top + 1)]

    def L(lit):  # noqa: N802
        return x[lit] if lit > 0 else x[-lit].Not()

    for c in clauses:
        md.add_bool_or([L(lit) for lit in c])
    for g in amos:
        md.add_at_most_one([L(lit) for lit in g])
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = timeout
    sv.parameters.num_workers = workers
    if lin is not None:
        sv.parameters.linearization_level = lin
    stt = sv.solve(md)
    return sv.status_name(stt), sv.num_conflicts, None


def check_model(clauses, model):
    pos = set(model)
    return all(any(lit in pos for lit in c) for c in clauses)


if __name__ == "__main__":
    path, solver, timeout = sys.argv[1], sys.argv[2], float(sys.argv[3])
    t0 = time.perf_counter()
    nv, cls = read_dimacs(path)
    t_read = time.perf_counter() - t0
    st = {}
    t0 = time.perf_counter()
    top, c2, amos = lift(nv, cls, st)
    t_lift = time.perf_counter() - t0
    t0 = time.perf_counter()
    if solver == "exact":
        r, conf, model = solve_exact(top, c2, amos, timeout)
    else:
        r, conf, model = solve_cpsat(top, c2, amos, timeout, workers=int(solver[5:] or 1))
    t_solve = time.perf_counter() - t0
    ok = None
    if model is not None:
        ok = check_model(cls, model)  # model must satisfy the ORIGINAL formula
    import json

    print(
        json.dumps(
            {
                "file": path,
                "solver": solver,
                "status": r,
                "conflicts": conf,
                "lift_s": round(t_lift, 3),
                "solve_s": round(t_solve, 3),
                "orig_vars": nv,
                "orig_clauses": len(cls),
                "model_checks_original": ok,
                **st,
            }
        )
    )
