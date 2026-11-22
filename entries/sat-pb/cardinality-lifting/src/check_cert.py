"""Independent certificate checker (shares no code with cardlift/certify).

Verifies that the ORIGINAL CNF F is unsatisfiable, given a certificate with
  defs:    (t, x, y)  meaning t <-> x & y, t fresh (> nv, increasing), var(x), var(y) <= nv
  clauses: each must be (a) a clause of F, (b) a definition clause, (c) R1: (-t1 | -t2) whose
           expansion (-x1 | -y1 | -x2 | -y2) is a clause of F, or (d) R2: obtained from a
           clause C of F
           by replacing literals y with t where -x in C and t <-> x & y
  amos:    sum(lits) <= 1, every pair (u, w) backed by a binary (-u | -w) of kind (a)-(c)
  farkas:  nonnegative rationals y_i over rows (clauses as sum>=1, amos as sum<=1) whose
           combination  c.x >= d  has  sum_j max(c_j, 0) < d , i.e. no x in [0,1]^n satisfies it.
Soundness: (b) is a conservative extension of F; (a)-(d) and the AMOs are implied by F plus the
definitions; an infeasible nonnegative combination over the box refutes them; hence F is UNSAT.
"""

import json
import lzma
import sys
from fractions import Fraction
from itertools import combinations


def read(path):
    op = lzma.open if path.endswith(".xz") else open
    nv, cls, cur = 0, [], []
    with op(path, "rt") as f:
        for line in f:
            if line.startswith("p"):
                nv = int(line.split()[2])
                continue
            if not line.strip() or line[0] in "c%":
                continue
            for tok in line.split():
                v = int(tok)
                if v == 0:
                    cls.append(frozenset(cur))
                    cur = []
                else:
                    cur.append(v)
    return nv, set(cls)


def fail(msg):
    print(json.dumps({"verified": False, "reason": msg}))
    sys.exit(1)


def main(cnf, certp):
    nv, F = read(cnf)
    cert = json.load(open(certp))
    if cert["nv"] != nv:
        fail("nv mismatch")
    D, defs, nxt = set(), {}, nv
    for t, x, y in cert["defs"]:
        if t != nxt + 1:
            fail(f"definition var {t} not fresh/sequential")
        if not (0 < abs(x) <= nv and 0 < abs(y) <= nv) or abs(x) == abs(y):
            fail("bad definition operands")
        nxt = t
        defs[t] = (x, y)
        D |= {frozenset((-t, x)), frozenset((-t, y)), frozenset((t, -x, -y))}
    top = nxt

    def r1(cl):
        if len(cl) != 2:
            return False
        a, b = tuple(cl)
        if a >= 0 or b >= 0 or -a not in defs or -b not in defs:
            return False
        x1, y1 = defs[-a]
        x2, y2 = defs[-b]
        return frozenset((-x1, -y1, -x2, -y2)) in F

    def r2(cl):
        if not any(lit > nv for lit in cl):
            return False
        orig = set()
        for lit in cl:
            if abs(lit) > nv:
                if lit < 0:
                    return False
                x, y = defs[lit]
                if -x in cl:
                    orig.add(y)
                elif -y in cl:
                    orig.add(x)
                else:
                    return False
            else:
                orig.add(lit)
        return frozenset(orig) in F

    def backed(cl):
        return cl in F or cl in D or r1(cl)

    rows = []
    for c in cert["clauses"]:
        cl = frozenset(c)
        if any(abs(lit) > top or lit == 0 for lit in cl):
            fail("literal out of range")
        if not (backed(cl) or r2(cl)):
            fail(f"unjustified clause {sorted(cl)[:6]}")
        rows.append((cl, ">=1"))
    for g in cert["amos"]:
        for u, w in combinations(g, 2):
            if not backed(frozenset((-u, -w))):
                fail(f"AMO pair ({u},{w}) not backed by a binary clause")
        rows.append((frozenset(g), "<=1"))

    if not cert.get("farkas"):
        fail("no Farkas multipliers")
    coef, d = {}, Fraction(0)
    for i_s, (num, den) in cert["farkas"].items():
        yv = Fraction(num, den)
        if yv < 0:
            fail("negative multiplier")
        lits, kind = rows[int(i_s)]
        # literal value: lit -> x_l ; -lit -> 1 - x_l.
        # kind >=1 : sum lits >= 1 ; kind <=1 : -sum lits >= -1
        sgn = 1 if kind == ">=1" else -1
        rhs = Fraction(1) if kind == ">=1" else Fraction(-1)
        for lit in lits:
            v = abs(lit)
            if lit > 0:
                coef[v] = coef.get(v, 0) + sgn * yv
            else:
                coef[v] = coef.get(v, 0) - sgn * yv
                rhs -= sgn
        d += yv * rhs
    maxlhs = sum(c for c in coef.values() if c > 0)
    if not maxlhs < d:
        fail(f"Farkas combination not contradictory: max lhs {maxlhs} >= rhs {d}")
    print(
        json.dumps(
            {
                "verified": True,
                "orig_vars": nv,
                "orig_clauses": len(F),
                "definitions": len(defs),
                "lifted_clauses": len(cert["clauses"]),
                "amos": len(cert["amos"]),
                "multipliers": len(cert["farkas"]),
                "slack": str(d - maxlhs),
            }
        )
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
