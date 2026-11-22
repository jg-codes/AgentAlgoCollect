import glob
import json
import subprocess
import sys
import time

for f in sorted(glob.glob("gen/*.cnf")):
    for cfg in ("exact_raw", "lift_exact"):
        t0 = time.time()
        try:
            p = subprocess.run(
                [sys.executable, "_worker.py", f, cfg, "30"],
                capture_output=True,
                text=True,
                timeout=150,
            )
            lit = [x for x in p.stdout.splitlines() if x.startswith("{")]
            r = json.loads(lit[-1]) if lit else {"status": "ERR " + p.stderr[-150:]}
        except subprocess.TimeoutExpired:
            r = {"status": "TIMEOUT"}
        print(
            f,
            cfg,
            r.get("status"),
            r.get("total_s"),
            "model_ok=",
            r.get("model_ok"),
            "amo=",
            r.get("R3_amo"),
            "ext=",
            r.get("extension_vars"),
            flush=True,
        )
