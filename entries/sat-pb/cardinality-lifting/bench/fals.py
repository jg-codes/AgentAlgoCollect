"""Falsification battery for the cardinality-lifting pre-pass. Writes JSONL rows to runs/."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import cardlift

RUNS = Path("runs")
RUNS.mkdir(exist_ok=True)


def stamp() -> dict:
    import exact  # noqa: F401
    import ortools
    import pysat

    cpu = subprocess.run(["lscpu"], capture_output=True, text=True).stdout
    model = next(
        (lit.split(":", 1)[1].strip() for lit in cpu.splitlines() if "Model name" in lit), ""
    )
    mem = next((lit.split()[1] for lit in open("/proc/meminfo") if lit.startswith("MemTotal")), "")
    return {
        "cpu": model,
        "cores": os.cpu_count(),
        "mem_kb": mem,
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "ortools": ortools.__version__,
        "pysat": pysat.__version__,
        "exact": "2.2.1 (PyPI wheel, no LP)",
        "kissat": subprocess.run(
            [os.environ.get("KISSAT", "kissat"), "--version"], capture_output=True, text=True
        ).stdout.strip(),
        "breakid": "meelgroup/breakid HEAD 2026-11-21",
        "threads": "single-thread unless stated",
        "seeds": "instance shuffles from cnfshuffle default RNG; perturbation seeds stated per row",
        "dtype": "integer / exact rational",
        "machine_id": platform.node(),
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def one(path: str, rules: str, solver: str, T: float, workers: int = 1) -> dict:
    nv, cls = cardlift.read_dimacs(path)
    t0 = time.perf_counter()
    st: dict = {}
    top, c2, amos = cardlift.lift(nv, cls, st, rules=rules)
    tl = time.perf_counter() - t0
    if solver == "exact":
        r, conf, model = cardlift.solve_exact(top, c2, amos, T)
    else:
        r, conf, model = cardlift.solve_cpsat(top, c2, amos, T, workers=workers, lin=2)
    ok = cardlift.check_model(cls, model) if model is not None else None
    st.pop("_defs", None)
    return {
        "file": path,
        "rules": rules,
        "solver": solver,
        "workers": workers,
        "status": r,
        "conflicts": conf,
        "lift_s": round(tl, 3),
        "total_s": round(time.perf_counter() - t0, 3),
        "model_ok": ok,
        **st,
    }


def sub(args: list[str], T: float) -> dict:
    """Run one() in a subprocess with a hard wall limit."""
    code = f"import json,fals;print(json.dumps(fals.one(*{args!r})))"
    try:
        p = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=T + 120
        )
        lines = [lit for lit in p.stdout.splitlines() if lit.startswith("{")]
        return json.loads(lines[-1]) if lines else {"status": "ERROR", "err": p.stderr[-300:]}
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT(wall)", "file": args[0], "rules": args[1]}


def write(name: str, rows: list[dict]) -> None:
    with open(RUNS / f"{name}.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "stamp":
        json.dump(stamp(), open(RUNS / "environment.json", "w"), indent=2)
    elif what == "ablation":
        files = [
            "gbd_inst/rphp_p6_r28.cnf",
            "gbd_inst/rphp_p20_r20.cnf",
            "gbd_inst/rphp4_065_shuffled.cnf",
            "gbd_inst/rphp5_040_shuffled.cnf",
            "gbd_inst/rphp_p60_r60.cnf",
            "gen/php13.cnf",
            "pert/rphp_pert_p20_r20_f15_s1.cnf",
        ]
        rows = []
        for f in files:
            for rules in ("", "3", "13", "123"):
                r = sub([f, rules, "exact", 30.0], 30)
                rows.append(r)
                print(f, rules, r.get("status"), r.get("total_s"), flush=True)
        write("ablation", rows)
    elif what == "threads":
        files = [
            "gbd_inst/rphp_p35_r35.cnf",
            "gbd_inst/rphp_p100_r100.cnf",
            "gbd_inst/rphp5_100_shuffled.cnf",
            "gbd_inst/rphp_p6_r540.cnf",
            "pert/rphp_pert_p60_r60_f15_s1.cnf",
        ]
        rows = []
        for f in files:
            for w in (1, 2, 8):
                r = sub([f, "123", "cpsat", 60.0, w], 60)
                rows.append(r)
                print(f, w, r.get("status"), r.get("total_s"), flush=True)
        write("threads_cpsat_lifted", rows)
    elif what == "repeats":
        rows = []
        for f in sorted(Path("gbd_inst").glob("*.cnf")):
            for rep in range(3):
                r = sub([str(f), "123", "exact", 300.0], 300)
                r["rep"] = rep
                rows.append(r)
            print(f.name, [x["total_s"] for x in rows[-3:]], flush=True)
        write("repeats_lift_exact", rows)
