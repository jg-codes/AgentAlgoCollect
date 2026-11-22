"""Soundness tests for the cardinality-lifting pre-pass and the certificate checker.

The equivalence test is exhaustive: for every assignment of the original variables it checks
that the original CNF is satisfied exactly when the lifted system is satisfied with the
extension variables set by their definitions, and that no other extension assignment works.
"""

from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import cardlift  # noqa: E402
import check_cert  # noqa: E402


def rphp_cnf(p: int, r: int, h: int) -> tuple[int, list[list[int]]]:
    """CNFgen-style RPHP: p pigeons, r resting places, h holes."""
    pv = lambda i, j: i * r + j + 1  # noqa: E731
    qv = lambda j, k: p * r + j * h + k + 1  # noqa: E731
    rv = lambda j: p * r + r * h + j + 1  # noqa: E731
    cls = [[pv(i, j) for j in range(r)] for i in range(p)]
    for j in range(r):
        cls += [[-pv(a, j), -pv(b, j)] for a, b in itertools.combinations(range(p), 2)]
        cls += [[-pv(i, j), rv(j)] for i in range(p)]
        cls.append([-rv(j)] + [qv(j, k) for k in range(h)])
    for k in range(h):
        for a, b in itertools.combinations(range(r), 2):
            cls.append([-rv(a), -rv(b), -qv(a, k), -qv(b, k)])
    return p * r + r * h + r, cls


def sat_clause(c, val):
    return any(val[abs(lit)] == (lit > 0) for lit in c)


def amo_ok(g, val):
    return sum(val[abs(lit)] == (lit > 0) for lit in g) <= 1


def lifted_ok(clauses, amos, val):
    return all(sat_clause(c, val) for c in clauses) and all(amo_ok(g, val) for g in amos)


def check_equivalence(nv, cls, rules="123"):
    st: dict = {}
    top, c2, amos = cardlift.lift(nv, [list(c) for c in cls], st, rules=rules)
    defs = st.get("_defs", [])
    ext = list(range(nv + 1, top + 1))
    assert len(ext) <= 8, "test instance too large for exhaustive extension check"
    for bits in itertools.product([False, True], repeat=nv):
        val = {i + 1: b for i, b in enumerate(bits)}
        orig = all(sat_clause(c, val) for c in cls)
        for t, x, y in defs:  # definitional values
            val[t] = (val[abs(x)] == (x > 0)) and (val[abs(y)] == (y > 0))
        assert lifted_ok(c2, amos, val) == orig
        for ebits in itertools.product([False, True], repeat=len(ext)):
            v2 = dict(val)
            v2.update(zip(ext, ebits, strict=True))
            if any(v2[e] != val[e] for e in ext):
                assert not lifted_ok(c2, amos, v2), "non-definitional extension accepted"
    return st


@pytest.mark.parametrize("p,r,h", [(2, 3, 1), (3, 3, 2), (2, 2, 2)])
@pytest.mark.parametrize("rules", ["3", "13", "123"])
def test_rphp_equivalence(p, r, h, rules):
    nv, cls = rphp_cnf(p, r, h)
    if nv > 14:
        pytest.skip("too many variables for exhaustive enumeration")
    check_equivalence(nv, cls, rules)


def test_rphp_rules_fire():
    # 3 pigeons, 4 resting places, 2 holes: 2 * C(4,2) = 12 hole clauses, 4 * 2 = 8 products,
    # and each of the 4 "occupied -> some hole" clauses gets both of its hole literals replaced.
    nv, cls = rphp_cnf(3, 4, 2)
    st: dict = {}
    cardlift.lift(nv, [list(c) for c in cls], st)
    assert st["R1_rewritten_4clauses"] == 12
    assert st["extension_vars"] == 8
    assert st["R2_substitutions"] == 8


@pytest.mark.parametrize("seed", range(30))
def test_random_cnf_equivalence(seed):
    rng = random.Random(seed)
    nv = 9
    cls = []
    for _ in range(rng.randint(8, 30)):
        k = rng.choice([2, 2, 3, 4, 4])
        vs = rng.sample(range(1, nv + 1), k)
        cls.append([v if rng.random() < 0.5 else -v for v in vs])
    st: dict = {}
    top, _, _ = cardlift.lift(nv, [list(c) for c in cls], st)
    if top - nv > 8:
        pytest.skip("too many extension variables for exhaustive check")
    check_equivalence(nv, cls)


def write_cnf(path: Path, nv: int, cls) -> None:
    path.write_text(
        f"p cnf {nv} {len(cls)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in cls)
    )


def test_certificate_accept_and_reject(tmp_path, capsys):
    pytest.importorskip("scipy")
    import certify

    nv, cls = rphp_cnf(4, 6, 3)
    cnf = tmp_path / "rphp.cnf"
    write_cnf(cnf, nv, cls)
    st: dict = {}
    top, c2, amos = cardlift.lift(nv, [list(c) for c in cls], st)
    ys, _ = certify.farkas(top, certify.lifted_system(top, c2, amos))
    assert ys is not None
    cert = {
        "nv": nv,
        "top": top,
        "defs": st["_defs"],
        "clauses": c2,
        "amos": amos,
        "farkas": {str(i): [f.numerator, f.denominator] for i, f in ys.items()},
    }
    good = tmp_path / "good.json"
    good.write_text(json.dumps(cert))
    check_cert.main(str(cnf), str(good))
    assert '"verified": true' in capsys.readouterr().out

    bad_variants = []
    b1 = json.loads(json.dumps(cert))
    b1["clauses"][0] = b1["clauses"][0][:-1]  # weakened clause, not derivable
    bad_variants.append(b1)
    b2 = json.loads(json.dumps(cert))
    k = next(iter(b2["farkas"]))
    b2["farkas"][k] = [0, 1]  # zeroed multiplier
    bad_variants.append(b2)
    b3 = json.loads(json.dumps(cert))
    b3["amos"][0] = b3["amos"][0] + [nv]  # unsupported clique member
    bad_variants.append(b3)
    for i, b in enumerate(bad_variants):
        path = tmp_path / f"bad{i}.json"
        path.write_text(json.dumps(b))
        with pytest.raises(SystemExit):
            check_cert.main(str(cnf), str(path))


def test_satisfiable_has_no_certificate():
    pytest.importorskip("scipy")
    import certify

    nv, cls = rphp_cnf(3, 5, 3)  # 3 pigeons, 3 holes: satisfiable
    top, c2, amos = cardlift.lift(nv, [list(c) for c in cls], {})
    ys, _ = certify.farkas(top, certify.lifted_system(top, c2, amos))
    assert ys is None
