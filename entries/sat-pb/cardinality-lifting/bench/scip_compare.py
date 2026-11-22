"""SCIP 10 on raw CNF (clauses as linear rows) vs the lifted system (clauses + AMO rows)."""

import json
import subprocess
import sys

FILES = [
    "gen/php9.cnf",
    "gen/mchess14.cnf",
    "gbd_inst/rphp_p20_r20.cnf",
    "gbd_inst/rphp4_065_shuffled.cnf",
    "gbd_inst/rphp_p35_r35.cnf",
    "pert/rphp_pert_p20_r20_f15_s1.cnf",
    "gen/kclique.cnf",
    "gen/cc.cnf",
]

WORKER = r"""
import sys, json, time
import cardlift
from pyscipopt import Model, quicksum
path, mode, T = sys.argv[1], sys.argv[2], float(sys.argv[3])
nv, cls = cardlift.read_dimacs(path)
t0 = time.perf_counter()
if mode == "lifted":
    top, cls2, amos = cardlift.lift(nv, cls, {})
else:
    top, cls2, amos = nv, cls, []
tl = time.perf_counter() - t0
m = Model(); m.hideOutput(); m.setParam("limits/time", T); m.setParam("parallel/maxnthreads", 1)
x = [None] + [m.addVar(vtype="B", name=f"x{i}") for i in range(1, top + 1)]
term = lambda lit: x[lit] if lit > 0 else 1 - x[-lit]  # noqa: E731
for c in cls2: m.addCons(quicksum(term(lit) for lit in c) >= 1)
for g in amos: m.addCons(quicksum(term(lit) for lit in g) <= 1)
m.optimize()
st = m.getStatus()
ok = None
if st == "optimal":
    sol = {i: m.getVal(x[i]) > 0.5 for i in range(1, nv + 1)}
    ok = all(any(sol[abs(lit)] == (lit > 0) for lit in c) for c in cls)
total = round(time.perf_counter() - t0, 3)
print(json.dumps({"status": st, "lift_s": round(tl, 3), "total_s": total,
                  "nodes": m.getNNodes(), "model_ok": ok}))
"""

if __name__ == "__main__":
    open("_scip_worker.py", "w").write(WORKER)
    rows = []
    for f in FILES:
        for mode in ("raw", "lifted"):
            try:
                p = subprocess.run(
                    [sys.executable, "_scip_worker.py", f, mode, "60"],
                    capture_output=True,
                    text=True,
                    timeout=200,
                )
                lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
                r = json.loads(lines[-1]) if lines else {"status": "ERROR", "err": p.stderr[-200:]}
            except subprocess.TimeoutExpired:
                r = {"status": "TIMEOUT(wall)"}
            r.update({"file": f, "mode": mode})
            rows.append(r)
            print(json.dumps(r), flush=True)
    with open("runs/scip_raw_vs_lifted.jsonl", "w") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
