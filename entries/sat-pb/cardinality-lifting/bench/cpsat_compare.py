"""CP-SAT 9.15 default parameters, 8 workers: raw CNF vs lifted system, 30 s."""

import json
import subprocess
import sys

FILES = [
    "gen/php9.cnf",
    "gen/mchess14.cnf",
    "gbd_inst/rphp_p20_r20.cnf",
    "gbd_inst/rphp4_065_shuffled.cnf",
    "gbd_inst/rphp_p35_r35.cnf",
    "gbd_inst/rphp_p100_r100.cnf",
    "gbd_inst/rphp_p6_r540.cnf",
    "pert/rphp_pert_p20_r20_f15_s1.cnf",
    "gen/kclique.cnf",
    "gen/cc.cnf",
]

WORKER = r"""
import sys, json, time
import cardlift
path, mode, T = sys.argv[1], sys.argv[2], float(sys.argv[3])
nv, cls = cardlift.read_dimacs(path)
t0 = time.perf_counter()
if mode == "lifted":
    top, c2, amos = cardlift.lift(nv, cls, {})
else:
    top, c2, amos = nv, cls, []
tl = time.perf_counter() - t0
r, conf, _ = cardlift.solve_cpsat(top, c2, amos, T, workers=8, lin=None)
total = round(time.perf_counter() - t0, 3)
print(json.dumps({"status": r, "lift_s": round(tl, 3), "total_s": total}))
"""

if __name__ == "__main__":
    open("_cpsat_worker.py", "w").write(WORKER)
    rows = []
    for f in FILES:
        for mode in ("raw", "lifted"):
            try:
                p = subprocess.run(
                    [sys.executable, "_cpsat_worker.py", f, mode, "30"],
                    capture_output=True,
                    text=True,
                    timeout=150,
                )
                lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
                r = json.loads(lines[-1]) if lines else {"status": "ERROR", "err": p.stderr[-200:]}
            except subprocess.TimeoutExpired:
                r = {"status": "TIMEOUT(wall)"}
            r.update({"file": f, "mode": mode})
            rows.append(r)
            print(json.dumps(r), flush=True)
    with open("runs/cpsat_raw_vs_lifted.jsonl", "w") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
