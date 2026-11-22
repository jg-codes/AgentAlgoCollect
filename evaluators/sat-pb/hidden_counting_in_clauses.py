"""Evaluator for the problem card sat-pb/hidden-counting-in-clauses.

A candidate is a Python program that is called as `python candidate.py <file.cnf>` and prints one
line, `s UNSATISFIABLE` or `s SATISFIABLE`. The evaluator generates a fixed, seeded instance set
with known answers, runs the candidate on each instance under a time limit and returns scores.

    python evaluators/sat-pb/hidden_counting_in_clauses.py path/to/candidate.py [--time-limit 10]

`evaluate(program_path)` returns a dict with `combined_score`, so the file can also be used
unchanged as the evaluator of an evolutionary code-search tool such as OpenEvolve.

Pairing each problem with an automatic evaluator follows AlphaEvolve (Novikov et al., 2025,
https://github.com/google-deepmind/alphaevolve_results).

Instances: relativized pigeonhole with P pigeons, R resting places and P - 1 holes, 15% of the
pigeon-place and place-hole options forbidden, clauses shuffled (unsatisfiable by construction);
plus satisfiable controls with P holes and nothing forbidden. A wrong answer on any instance sets
the score to zero.
"""

from __future__ import annotations

import itertools
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

UNSAT_SIZES = ((5, 8), (6, 10), (8, 12), (10, 10), (12, 16), (16, 16))
UNSAT_SEEDS = (1, 2)
SAT_SIZES = ((5, 8), (8, 12), (12, 16))
FORBIDDEN = 0.15


def rphp(p: int, r: int, h: int, forbid: float, seed: int) -> tuple[int, list[list[int]]]:
    """Relativized pigeonhole in clauses; `forbid` is the share of options removed."""
    rng = random.Random(seed)

    def pv(i: int, j: int) -> int:
        return i * r + j + 1

    def qv(j: int, k: int) -> int:
        return p * r + j * h + k + 1

    def rv(j: int) -> int:
        return p * r + r * h + j + 1

    cls = [[pv(i, j) for j in range(r)] for i in range(p)]
    for j in range(r):
        cls += [[-pv(a, j), -pv(b, j)] for a, b in itertools.combinations(range(p), 2)]
        cls += [[-pv(i, j), rv(j)] for i in range(p)]
        cls.append([-rv(j)] + [qv(j, k) for k in range(h)])
    for k in range(h):
        for a, b in itertools.combinations(range(r), 2):
            cls.append([-rv(a), -rv(b), -qv(a, k), -qv(b, k)])
    cls += [[-v] for v in range(1, p * r + r * h + 1) if rng.random() < forbid]
    for c in cls:
        rng.shuffle(c)
    rng.shuffle(cls)
    return p * r + r * h + r, cls


def instances() -> list[tuple[str, str, int, list[list[int]]]]:
    out = []
    for (p, r), seed in itertools.product(UNSAT_SIZES, UNSAT_SEEDS):
        nv, cls = rphp(p, r, p - 1, FORBIDDEN, seed)
        out.append((f"unsat_p{p}_r{r}_s{seed}", "UNSATISFIABLE", nv, cls))
    for p, r in SAT_SIZES:
        nv, cls = rphp(p, r, p, 0.0, 1)
        out.append((f"sat_p{p}_r{r}", "SATISFIABLE", nv, cls))
    return out


def run_candidate(program_path: str, cnf: Path, time_limit: float) -> tuple[str, float]:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, program_path, str(cnf)],
            capture_output=True,
            text=True,
            timeout=time_limit,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", time_limit
    elapsed = time.perf_counter() - start
    for line in proc.stdout.splitlines():
        if line.startswith("s "):
            return line[2:].strip(), elapsed
    return "NO ANSWER", elapsed


def evaluate(program_path: str, time_limit: float = 10.0, **_: object) -> dict[str, object]:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, expected, nv, cls in instances():
            cnf = Path(tmp) / f"{name}.cnf"
            body = "".join(" ".join(map(str, c)) + " 0\n" for c in cls)
            cnf.write_text(f"p cnf {nv} {len(cls)}\n{body}")
            answer, seconds = run_candidate(program_path, cnf, time_limit)
            rows.append(
                {
                    "instance": name,
                    "expected": expected,
                    "answer": answer,
                    "seconds": round(seconds, 3),
                }
            )
    answered = [r for r in rows if r["answer"] in ("SATISFIABLE", "UNSATISFIABLE")]
    wrong = [r for r in answered if r["answer"] != r["expected"]]
    solved = [r for r in answered if r["answer"] == r["expected"]]
    par2 = sum(float(str(r["seconds"])) if r in solved else 2 * time_limit for r in rows) / len(
        rows
    )
    return {
        "combined_score": 0.0 if wrong else len(solved) / len(rows),
        "solved": len(solved),
        "solved_unsat": sum(1 for r in solved if r["expected"] == "UNSATISFIABLE"),
        "solved_sat": sum(1 for r in solved if r["expected"] == "SATISFIABLE"),
        "instances": len(rows),
        "wrong_answers": len(wrong),
        "par2_seconds": round(par2, 3),
        "time_limit_seconds": time_limit,
        "rows": rows,
    }


if __name__ == "__main__":
    limit = (
        float(sys.argv[sys.argv.index("--time-limit") + 1]) if "--time-limit" in sys.argv else 10.0
    )
    print(json.dumps(evaluate(sys.argv[1], time_limit=limit), indent=2))
