# Benchmark drivers

`reproduce.sh` reproduces the flagship result with one command. The other scripts produced the
remaining files in `../evidence/`. They expect to run from a `work/` folder next to this one, write
to `work/runs/`, and need the instance sets generated first. They are kept for inspection and reuse
and are not a one-command pipeline.

| Evidence file | Produced by | Needs |
|---|---|---|
| `perturbed_vs_breakid.txt`, `seeds.tsv` | `gen_perturbed.py`, `seeds.sh` | Kissat, BreakID |
| `res_lift_exact.jsonl`, `res_exact_raw.jsonl`, `res_cadical.jsonl` | `gbd_suite.py gen`, then `gbd_suite.py run <config>` | Exact, PySAT |
| `res_breakid_kissat.tsv`, `res_kissat_raw.tsv`, `p90_long.txt` | `run_kissat.sh` | Kissat, BreakID |
| `cert_results.txt` | `../src/certify.py` and `../src/check_cert.py` per instance | SciPy |
| `ablation.jsonl`, `threads_cpsat_lifted.jsonl`, `repeats_lift_exact.jsonl`, `environment.json` | `fals.py` | Exact, OR-Tools |
| `generality.txt`, `cc_repeats.txt` | `gen_generality.sh`, `gen_run.py` | CNFgen, Exact |
| `exact_option_sweep.jsonl` | `exact_sweep.py` | Exact |
| `scip_raw_vs_lifted.jsonl`, `cpsat_raw_vs_lifted.jsonl` | `scip_compare.py`, `cpsat_compare.py` | PySCIPOpt, OR-Tools |
| `results.csv`, `php_mchess_lifted_exact.log` | `../src/baselines.py run`, an early clique-only prototype | Exact, PySAT, OR-Tools |
| `../TABLES.md` | `summarize.py` (reads only `../evidence/`) | none |

Versions used: Kissat 4.0.4, BreakID commit 1a022d0, Exact 2.2.1 (PyPI wheel, built without its LP
solver), OR-Tools 9.15, PySCIPOpt 6.3.0 (SCIP 10.0), CNFgen 0.9.6; full machine stamp in
`../evidence/environment.json`. Instance shuffling (`cnfshuffle`) is unseeded.
