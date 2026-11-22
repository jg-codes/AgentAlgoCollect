"""Regenerate the 55 GBD 'relativized-pigeon-hole' instances with CNFgen (parameters from the
GBD file names; rphp_pP_rR uses P-1 holes per sat-heritage/benchs-generators; rphpK_NNN_shuffled
read as K pigeons, NNN resting places, K-1 holes, reshuffled) and run baselines vs lift pre-pass.

Usage: python3 gbd_suite.py gen
       python3 gbd_suite.py run <config> <timeout> <out.jsonl>
"""

import json
import os
import subprocess
import sys
import time

GBD = [  # (gbd filename, gbd status)
    ("rphp4_065_shuffled", "unsat"),
    ("rphp_p100_r100", "unknown"),
    ("rphp4_130_shuffled", "sat"),
    ("rphp4_100_shuffled", "unsat"),
    ("rphp_p8_r170.sanitized", "unsat"),
    ("rphp_p20_r20", "unsat"),
    ("rphp4_110_shuffled", "unsat"),
    ("rphp5_080_shuffled", "unsat"),
    ("rphp_p60_r60", "unsat"),
    ("rphp4_070_shuffled", "unsat"),
    ("rphp_p95_r95", "unknown"),
    ("rphp_p8_r160.sanitized", "unsat"),
    ("rphp4_140_shuffled", "unsat"),
    ("rphp_p6_r300", "unknown"),
    ("rphp4_135_shuffled", "unsat"),
    ("rphp_p35_r35", "unknown"),
    ("rphp_p30_r30", "unsat"),
    ("rphp4_155_shuffled", "unsat"),
    ("rphp4_145_shuffled", "unsat"),
    ("rphp5_100_shuffled", "unknown"),
    ("rphp4_080_shuffled", "unsat"),
    ("rphp5_095_shuffled", "unknown"),
    ("rphp4_095_shuffled", "unsat"),
    ("rphp4_150_shuffled", "unsat"),
    ("rphp_p6_r540", "unknown"),
    ("rphp4_125_shuffled", "unsat"),
    ("rphp4_105_shuffled", "unsat"),
    ("rphp5_100_shuffled-sc2016", "unknown"),
    ("rphp5_090_shuffled", "unknown"),
    ("rphp5_040_shuffled", "unsat"),
    ("rphp_p90_r90", "unknown"),
    ("rphp5_055_shuffled", "unsat"),
    ("rphp_p14_r14", "unsat"),
    ("rphp5_075_shuffled", "unsat"),
    ("rphp4_115_shuffled", "unsat"),
    ("rphp4_160_shuffled", "unsat"),
    ("rphp_p110_r110", "unknown"),
    ("rphp5_105_shuffled", "sat"),
    ("rphp5_045_shuffled", "unsat"),
    ("rphp4_075_shuffled", "unsat"),
    ("rphp5_070_shuffled", "unsat"),
    ("rphp5_065_shuffled", "sat"),
    ("rphp5_050_shuffled", "unsat"),
    ("rphp_p6_r28", "unsat"),
    ("rphp5_035_shuffled", "unsat"),
    ("rphp5_085_shuffled", "unsat"),
    ("rphp_p25_r25", "unsat"),
    ("rphp_p105_r105", "unknown"),
    ("rphp5_060_shuffled", "unsat"),
    ("rphp_p8_r250", "unsat"),
    ("rphp_p115_r115", "unknown"),
    ("rphp4_085_shuffled", "unsat"),
    ("rphp4_120_shuffled", "unsat"),
    ("rphp_p8_r25", "unknown"),
    ("rphp4_090_shuffled", "unsat"),
]


def params(name):
    base = name.split(".")[0]
    if base.startswith("rphp_p"):
        p, r = base[6:].split("_r")
        p, r = int(p), int(r)
        return p, r, p - 1, False
    k, rest = base[4:].split("_", 1)
    return int(k), int(rest.split("_")[0]), int(k) - 1, True


def gen():
    os.makedirs("gbd_inst", exist_ok=True)
    for i, (name, _) in enumerate(GBD):
        p, r, h, shuf = params(name)
        out = f"gbd_inst/{name}.cnf"
        if os.path.exists(out):
            continue
        raw = out + ".raw"
        with open(raw, "w") as f:
            subprocess.run(["cnfgen", "-q", "rphp", str(p), str(r), str(h)], stdout=f, check=True)
        if shuf:
            subprocess.run(["cnfshuffle", "-i", raw, "-o", out, "-s", str(1000 + i)], check=False)
            if not os.path.exists(out) or os.path.getsize(out) == 0:
                subprocess.run(["cnfshuffle", "-i", raw, "-o", out], check=True)
            os.remove(raw)
        else:
            os.rename(raw, out)
        print(name, p, r, h, shuf, os.path.getsize(out), flush=True)


WORKER = r"""
import sys, json, time
sys.path.insert(0, ".")
import cardlift, baselines
path, cfg, T = sys.argv[1], sys.argv[2], float(sys.argv[3])
nv, cls = cardlift.read_dimacs(path)
t0 = time.perf_counter(); st = {}; extra = {}
if cfg == "cadical":
    r, conf = baselines.run_cadical(nv, cls, T)
elif cfg == "exact_raw":
    r, conf = baselines.run_exact(nv, cls, T)
else:
    top, c2, amos = cardlift.lift(nv, cls, st); extra["lift_s"] = round(time.perf_counter() - t0, 3)
    st.pop("_defs", None)
    t1 = time.perf_counter()
    if cfg == "lift_exact":
        r, conf, model = cardlift.solve_exact(top, c2, amos, T)
        if model is not None: extra["model_ok"] = cardlift.check_model(cls, model)
    else:
        r, conf, _ = cardlift.solve_cpsat(top, c2, amos, T, workers=1, lin=2)
    extra["solve_s"] = round(time.perf_counter() - t1, 3)
total = round(time.perf_counter() - t0, 3)
print(json.dumps({"status": r, "conflicts": conf, "total_s": total, **extra, **st}))
"""


def run(cfg, timeout, out):
    done = set()
    if os.path.exists(out):
        done = {json.loads(lit)["name"] for lit in open(out)}
    with open("_worker.py", "w") as f:
        f.write(WORKER)
    for name, gstat in GBD:
        if name in done:
            continue
        path = f"gbd_inst/{name}.cnf"
        t0 = time.perf_counter()
        try:
            p = subprocess.run(
                [sys.executable, "_worker.py", path, cfg, str(timeout)],
                capture_output=True,
                text=True,
                timeout=timeout + (30 if cfg == "cadical" else 120),
            )
            lines = [lit for lit in p.stdout.splitlines() if lit.startswith("{")]
            r = json.loads(lines[-1]) if lines else {"status": "ERROR", "err": p.stderr[-300:]}
        except subprocess.TimeoutExpired:
            r = {"status": "TIMEOUT"}
        r.update(
            {"name": name, "gbd": gstat, "cfg": cfg, "wall_s": round(time.perf_counter() - t0, 2)}
        )
        with open(out, "a") as f:
            f.write(json.dumps(r) + "\n")
        print(name, gstat, r.get("status"), r.get("total_s"), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen()
    else:
        run(sys.argv[2], float(sys.argv[3]), sys.argv[4])
