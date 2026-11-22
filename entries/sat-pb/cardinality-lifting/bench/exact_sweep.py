"""Does any Exact 2.2.1 option recover what the lifting pre-pass does? Raw CNF input, 30 s."""

import json
import subprocess
import sys

CONFIGS = {
    "default": [],
    "amo_unlimited": [("inp-atmostone", "1")],
    "amo_unlimited_basetime10": [("inp-atmostone", "1"), ("inp-basetime", "10")],
    "probing_unlimited": [("inp-probing", "1")],
    "dominance_unlimited": [("inp-dombreaklim", "-1")],
    "lp_full": [("lp-budget", "1")],
    "lp_full_amo": [("lp-budget", "1"), ("inp-atmostone", "1")],
    "ca_liftdegree": [("ca-liftdegree", "1")],
    "ca_multiply": [("ca-multiply", "1")],
    "ca_weaken_nonimplying": [("ca-weaken-nonimplying", "1")],
    "bits_cardinality": [("bits-learned", "1")],
    # lp-* options are listed in the binary but rejected by the PyPI build ("Unknown option").
    "all_without_lp": [
        ("inp-atmostone", "1"),
        ("inp-basetime", "10"),
        ("inp-probing", "1"),
        ("inp-dombreaklim", "-1"),
        ("ca-liftdegree", "1"),
        ("ca-multiply", "1"),
    ],
}
FILES = ["gen/php9.cnf", "gbd_inst/rphp_p20_r20.cnf", "gen/mchess14.cnf"]

WORKER = r"""
import sys, json, exact, cardlift
path, opts, T = sys.argv[1], json.loads(sys.argv[2]), float(sys.argv[3])
nv, cls = cardlift.read_dimacs(path)
try:
    s = exact.Exact([tuple(o) for o in opts])
except Exception as e:
    print(json.dumps({"status": "OPTION_ERROR", "err": str(e)[:200]})); sys.exit()
for i in range(1, nv + 1): s.addVariable(f"x{i}")
for c in cls:
    terms = [(1 if lit > 0 else -1, f"x{abs(lit)}") for lit in c]
    s.addConstraint(terms, True, 1 - sum(lit < 0 for lit in c))
r = s.runFull(False, T); st = dict(s.getStats())
amo = st.get("detected at-most-ones")
print(json.dumps({"status": r, "conflicts": st.get("conflicts"), "amo": amo}))
"""

if __name__ == "__main__":
    open("_sweep_worker.py", "w").write(WORKER)
    rows = []
    for f in FILES:
        for name, opts in CONFIGS.items():
            try:
                p = subprocess.run(
                    [sys.executable, "_sweep_worker.py", f, json.dumps(opts), "30"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
                r = json.loads(lines[-1]) if lines else {"status": "ERROR", "err": p.stderr[-200:]}
            except subprocess.TimeoutExpired:
                r = {"status": "TIMEOUT(wall)"}
            r.update({"file": f, "config": name})
            rows.append(r)
            print(json.dumps(r), flush=True)
    with open("runs/exact_option_sweep.jsonl", "w") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
