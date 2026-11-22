"""Reproducer for reports/upstream-exact-issue.md (copied verbatim from the draft)."""

import itertools

import exact


def php(n, add_amo, keep_binaries):
    # n+1 pigeons, n holes; x(p,h) = p*n+h+1
    s = exact.Exact()

    def v(p, h):
        return f"x{p * n + h + 1}"

    for p in range(n + 1):
        for h in range(n):
            s.addVariable(v(p, h))
    for p in range(n + 1):
        s.addConstraint([(1, v(p, h)) for h in range(n)], True, 1)
    for h in range(n):
        if keep_binaries:
            for a, b in itertools.combinations(range(n + 1), 2):
                s.addConstraint([(-1, v(a, h)), (-1, v(b, h))], True, -1)
        if add_amo:
            s.addConstraint([(1, v(p, h)) for p in range(n + 1)], False, 0, True, 1)
    r = s.runFull(False, 60)
    return r, dict(s.getStats()).get("conflicts")


for n in (9, 12, 20):
    print(n, "binaries only", php(n, False, True))
    print(n, "binaries + AMO", php(n, True, True))
    print(n, "AMO only", php(n, True, False))
