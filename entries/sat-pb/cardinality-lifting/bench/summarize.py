"""Build TABLES.md from the saved run files in evidence/. Every reported number comes from here."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "evidence"
sys.path.insert(0, str(HERE))
from gbd_suite import GBD  # noqa: E402


def jl(name):
    return [json.loads(line) for line in open(RUNS / name)]


def tsv(name):
    rows = {}
    for line in open(RUNS / name):
        f = line.rstrip("\n").split("\t")
        rows[f[0]] = f[1:]
    return rows


def group(name):
    return "2016 shuffled" if "shuffled" in name else "2022-24 rphp_pP_rR"


def gbd_table():
    ours = {r["name"]: r for r in jl("res_lift_exact.jsonl")}
    exr = {r["name"]: r for r in jl("res_exact_raw.jsonl")}
    cad = {r["name"]: r for r in jl("res_cadical.jsonl")}
    bk = tsv("res_breakid_kissat.tsv")
    kr = tsv("res_kissat_raw.tsv")
    cert = {ln.split()[0]: '"verified": true' in ln for ln in open(RUNS / "cert_results.txt")}
    rep = defaultdict(list)
    for r in jl("repeats_lift_exact.jsonl"):
        rep[Path(r["file"]).stem].append(r["total_s"])
    agg = defaultdict(Counter)
    meds = defaultdict(list)
    for n, g in GBD:
        k = (group(n), g)
        a = agg[k]
        a["n"] += 1
        a["ours"] += ours[n]["status"] == "UNSAT"
        a["cert"] += cert.get(n, False)
        a["bk"] += bk[n][0] == "UNSATISFIABLE"
        a["exr"] += exr[n]["status"] == "UNSAT"
        a["cad_run"] += n in cad
        a["cad"] += cad.get(n, {}).get("status") == "UNSAT"
        a["kr_run"] += n in kr
        a["kr"] += kr.get(n, [""])[0] == "UNSATISFIABLE"
        meds[k].append(statistics.median(rep[n]))
    out = [
        "| Group | GBD status | n | Ours solved / certified | Ours median s (max) | "
        "BreakID+Kissat 60 s | Kissat 30 s | CaDiCaL 20 s | Exact 20 s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tot = Counter()
    for k in sorted(agg):
        a = agg[k]
        tot.update(a)
        out.append(
            f"| {k[0]} | {k[1]} | {a['n']} | {a['ours']} / {a['cert']} | "
            f"{statistics.median(meds[k]):.2f} ({max(meds[k]):.2f}) | {a['bk']}/{a['n']} | "
            f"{a['kr']}/{a['kr_run']} run | {a['cad']}/{a['cad_run']} run | "
            f"{a['exr']}/{a['n']} |"
        )
    allm = [m for v in meds.values() for m in v]
    out.append(
        f"| **all** | | {tot['n']} | {tot['ours']} / {tot['cert']} | "
        f"{statistics.median(allm):.2f} ({max(allm):.2f}) | {tot['bk']}/{tot['n']} | "
        f"{tot['kr']}/{tot['kr_run']} run | {tot['cad']}/{tot['cad_run']} run | "
        f"{tot['exr']}/{tot['n']} |"
    )
    fails = sorted(n for n, _ in GBD if bk[n][0] != "UNSATISFIABLE")
    out.append("")
    out.append("BreakID+Kissat timeouts at 60 s: " + ", ".join(fails))
    out.append(
        "Long run p90_r90 BreakID+Kissat: " + " ".join(open(RUNS / "p90_long.txt").read().split())
    )
    return "\n".join(out)


def perturbed_table():
    rows = []
    for ln in open(RUNS / "perturbed_vs_breakid.txt"):
        p = [x.strip() for x in ln.split("|")]
        rows.append(
            (
                p[0],
                "UNSAT" in p[1] and "TIMEOUT" not in p[1],
                p[2].split()[1],
                float(p[2].split()[2]),
                "true" in p[3],
            )
        )
    for n, f in tsv("seeds.tsv").items():
        if "pert" in n:
            rows.append(
                (
                    n,
                    f[0] == "UNSATISFIABLE",
                    f[2].split()[0],
                    float(f[2].split()[1]),
                    f[3] == "true",
                )
            )
    bk = sum(r[1] for r in rows)
    ours = sum(r[2] == "UNSAT" for r in rows)
    cert = sum(r[4] for r in rows)
    return (
        f"| Set | n | BreakID+Kissat 60 s | Ours solved | Ours certified | Ours max s |\n"
        f"|---|---:|---:|---:|---:|---:|\n"
        f"| Perturbed RPHP (15% forbidden, shuffled; 6 sizes x 2 seeds + 2 sizes x 5 seeds) "
        f"| {len(rows)} | {bk} | {ours} | {cert} | {max(r[3] for r in rows):.2f} |"
    )


def reshuffle_table():
    out = [
        "| Instance (5 reshuffles each) | BreakID+Kissat solved, max s | "
        "Ours solved, max s | Certified |",
        "|---|---:|---:|---:|",
    ]
    by = defaultdict(list)
    for n, f in tsv("seeds.tsv").items():
        if "shuf" in n and "pert" not in n:
            by[n.rsplit("_shuf", 1)[0]].append(f)
    for b, fs in sorted(by.items()):
        out.append(
            f"| {b} | {sum(f[0] == 'UNSATISFIABLE' for f in fs)}/5, "
            f"{max(float(f[1]) for f in fs):.2f} | "
            f"{sum(f[2].startswith('UNSAT') for f in fs)}/5, "
            f"{max(float(f[2].split()[1]) for f in fs):.2f} | "
            f"{sum(f[3] == 'true' for f in fs)}/5 |"
        )
    return "\n".join(out)


def ablation_table():
    rows = jl("ablation.jsonl")
    out = ["| Instance | none (stock Exact) | R3 | R1+R3 | R1+R2+R3 |", "|---|---|---|---|---|"]
    by = defaultdict(dict)
    for r in rows:
        by[Path(r["file"]).stem][r["rules"]] = r
    for n, d in by.items():
        cells = [f"{d[k]['status']} {d[k]['total_s']:.2f}s" for k in ("", "3", "13", "123")]
        out.append(f"| {n} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def threads_table():
    out = [
        "| Instance (lifted, CP-SAT lin 2) | 1 worker | 2 workers | 8 workers |",
        "|---|---|---|---|",
    ]
    by = defaultdict(dict)
    for r in jl("threads_cpsat_lifted.jsonl"):
        by[Path(r["file"]).stem][r["workers"]] = r
    for n, d in by.items():
        out.append(
            f"| {n} | "
            + " | ".join(f"{d[w]['status']} {d[w]['total_s']:.1f}s" for w in (1, 2, 8))
            + " |"
        )
    return "\n".join(out)


def generality_table():
    out = [
        "| Instance | Stock Exact 30 s | Lifted Exact 30 s | AMOs | Extension vars | "
        "Model checks original |",
        "|---|---|---|---:|---:|---|",
    ]
    rows = defaultdict(dict)
    for ln in open(RUNS / "generality.txt"):
        p = ln.split()
        rows[Path(p[0]).stem][p[1]] = p
    for n, d in rows.items():
        a, b = d["exact_raw"], d["lift_exact"]
        out.append(
            f"| {n} | {a[2]} {a[3]}s | {b[2]} {b[3]}s | {b[7]} | {b[9]} | "
            f"{b[5].split('=')[-1] or b[6]} |"
        )
    return "\n".join(out)


def php_mchess_table():
    best = {}
    for r in csv.DictReader(open(RUNS / "results.csv")):
        k = (r["family"], r["solver"], r["encoding"])
        best.setdefault(k, "-")
        if r["status"] == "UNSAT" and float(r["seconds"]) <= 60:
            best[k] = r["n"]
    out = ["| Family | Solver | Encoding | Largest n solved <= 60 s |", "|---|---|---|---:|"]
    out += [f"| {f} | {s} | {e} | {n} |" for (f, s, e), n in best.items()]
    return "\n".join(out)


def exact_sweep_table():
    by = defaultdict(dict)
    for r in jl("exact_option_sweep.jsonl"):
        by[r["config"]][Path(r["file"]).stem] = r
    files = ["php9", "rphp_p20_r20", "mchess14"]
    out = [
        "| Exact 2.2.1 setting (raw CNF, 30 s) | " + " | ".join(files) + " |",
        "|---|" + "---|" * len(files),
    ]
    for cfg, d in by.items():
        cells = []
        for f in files:
            r = d.get(f, {})
            st = r.get("status", "-")
            cells.append(st if st != "TIMEOUT" else f"TIMEOUT ({int(r['conflicts'])} conflicts)")
        out.append(f"| {cfg} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def raw_vs_lifted_table(name, label):
    by = defaultdict(dict)
    for r in jl(name):
        by[Path(r["file"]).stem][r["mode"]] = r
    out = [f"| Instance | {label} raw | {label} lifted (pre-pass s) |", "|---|---|---|"]
    for n, d in by.items():
        a, b = d["raw"], d["lifted"]
        out.append(
            f"| {n} | {a['status']} {a['total_s']:.2f}s | "
            f"{b['status']} {b['total_s']:.2f}s ({b['lift_s']:.2f}) |"
        )
    return "\n".join(out)


def cc_repeats_table():
    rows = defaultdict(list)
    for ln in open(RUNS / "cc_repeats.txt"):
        cfg, st, t, conf = ln.split()
        rows[cfg].append((st, float(t), float(conf)))
    out = [
        "| Clique-colouring, Exact 60 s, 3 repeats | status | median s | conflicts |",
        "|---|---|---:|---:|",
    ]
    for cfg, rs in rows.items():
        out.append(
            f"| {cfg} | {rs[0][0]} | {statistics.median(r[1] for r in rs):.2f} | {int(rs[0][2])} |"
        )
    return "\n".join(out)


if __name__ == "__main__":
    env = json.load(open(RUNS / "environment.json"))
    parts = [
        "# Tables (generated by bench/summarize.py from evidence/; do not edit by hand)",
        "Environment: " + ", ".join(f"{k}={v}" for k, v in env.items()),
        "## T1 GBD relativized-pigeon-hole, 55 instances (regenerated)",
        gbd_table(),
        "## T2 Perturbed RPHP (own family, built after the method was fixed)",
        perturbed_table(),
        "## T3 Reshuffle sensitivity",
        reshuffle_table(),
        "## T4 Ablation (Exact, 30 s)",
        ablation_table(),
        "## T5 Thread sensitivity of CP-SAT on the lifted system",
        threads_table(),
        "## T6 Generality and regressions",
        generality_table(),
        "## T7 PHP and mutilated chessboard sweep",
        php_mchess_table(),
        "## T8 Does an existing Exact setting do the split?",
        exact_sweep_table(),
        "## T9 SCIP 10.0 (PySCIPOpt 6.3.0), 1 thread, 60 s",
        raw_vs_lifted_table("scip_raw_vs_lifted.jsonl", "SCIP"),
        "## T10 CP-SAT 9.15, default parameters, 8 workers, 30 s",
        raw_vs_lifted_table("cpsat_raw_vs_lifted.jsonl", "CP-SAT"),
        "## T11 Overhead on clique-colouring is propagation cost, not pre-pass time",
        cc_repeats_table(),
    ]
    (HERE.parent / "TABLES.md").write_text("\n\n".join(parts) + "\n")
    print((HERE.parent / "TABLES.md").read_text())
