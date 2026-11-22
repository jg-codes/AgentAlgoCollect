# Counting where symmetry breaking fails

**Status: candidate** (3 of 7 gate criteria; see `entry.yaml`)
**Problem card:** [hidden counting in clauses](../../../problems/sat-pb/hidden-counting-in-clauses.yaml)
**Improves:** robustness, verifiability. **Costs:** added time on formulas without the structure (see Limits).

## Problem

Clause-learning SAT solvers cannot count efficiently: "101 pigeons do not fit into 100 holes",
written as clauses, takes them exponentially long (Haken 1985). Symmetry breaking is a common remedy,
and it depends on the instance being regular.

## Result

Relativized pigeonhole with 15% of the options forbidden at random (symmetry broken, still
unsatisfiable), 22 instances, 60 s limit, one 2-core machine:

| Method | Refuted |
|---|---|
| BreakID + Kissat 4.0.4 (symmetry breaking) | 0 / 22 |
| This rewrite + Exact 2.2.1 | 22 / 22, each within 2.01 s |

For all 22, a certificate was then produced and verified in a separate, untimed step. The 60 s
limit for the baseline includes the symmetry-breaking time. The family is our own construction.

Supporting result: on 55 instances regenerated with CNFgen from the file-name parameters of the GBD
family "relativized-pigeon-hole", 55/55 against 46/55. These are **not the original benchmark
files**: three carry names that GBD lists as satisfiable, while our regenerated versions are
unsatisfiable, so at least that sub-family differs from the originals.
All tables: [TABLES.md](TABLES.md), generated from `evidence/` by `bench/summarize.py`.

## Method

Three rewrite rules that keep the formula equivalent and contain no family-specific code:

1. **Product extension.** A 4-literal clause whose literals split into two recurring pairs becomes
   a 2-literal clause over two new variables, each defined as the conjunction of one pair.
2. **Substitution.** Where a clause contains ¬x and y, and t ≡ x ∧ y is defined, y is replaced by t.
3. **Literal cliques.** Groups of 2-literal clauses that forbid every pair in a set become one
   "at most one" constraint, and the covered clauses are removed.

The rewritten system is infeasible as a linear program. `src/certify.py` extracts the multipliers,
and `src/check_cert.py`, which shares no code with the rewrite, verifies them in exact arithmetic
against the original formula. Soundness argument: [docs/soundness.md](docs/soundness.md).

Rule 1 is narrow: it only matches 4-literal clauses with recurring literal pairs. Among the tested
families it applies to relativized pigeonhole and to Tseitin formulas (no benefit there).

On the relativized pigeonhole instances tested, the rewritten formulas were also refuted by SCIP 10.0
(4 of 4, against 1 of 4 unmodified) and OR-Tools CP-SAT 9.15 (6 of 6, against 2 of 6); single runs,
TABLES.md T9 and T10. Both were slower on the rewritten k-clique formula.

## Reproduce

```bash
pip install exact cnfgen scipy
bash bench/reproduce.sh          # about one minute; prints instances=22 refuted=22 certified=22
```

This reproduces the flagship row only. `bench/README.md` maps every evidence file to the script
that produced it; those runs need more setup and are not one command.

```bash
KISSAT=/path/to/kissat BREAKID=/path/to/breakid bash bench/reproduce.sh   # adds the baseline
```

## Limits

- 60 s limits, not the 5000 s competition protocol; no long baseline run on the 22 flagship instances.
  On one of the 55 (p90_r90), BreakID + Kissat succeeds when given 238 s.
- Baselines not run: SBVA, SATSUMA, RoundingSat with cardinality detection, Exact built with its
  LP solver, and the family-specific solver of Green et al.
- The 55 regenerated instances are not the original benchmark files (see above).
- The perturbation only adds unit clauses. Simplifying by unit propagation before the rewrite is untested.
- Instance shuffling is unseeded, so regenerated instances differ in order from the measured ones.
- Cost on formulas without the structure: k-clique 0.04 → 0.54 s and clique-colouring 24.9 → 27.2 s
  in Exact (TABLES.md T6), so the rewrite should be an opt-in step.
- Only crafted families so far. Whether the pattern occurs in real-world models is unmeasured.
- One machine; most timings are single runs.

## How each claim is backed

| Claim | Kind |
|---|---|
| 22/22 and 55/55 refuted; baseline 0/22 and 46/55 | measured |
| Each reported refutation is correct | machine-checked by `src/check_cert.py` (our own independent checker, not a proof assistant) |
| The rewrite rules preserve satisfiability for every formula | argued in `docs/soundness.md`; tested exhaustively on small formulas |
| When the rewrite finds the intended pairs and cliques, the rewritten system is infeasible as a linear program for every size | argued in `docs/soundness.md`; observed on all 92 tested instances |

Open invitations: formalize the two argued claims in Lean, and rerun on the original benchmark files.

## Prior work

The parts are known: cardinality detection (Biere et al. 2014; Elffers and Nordström 2020), removal
of covered clauses (Reeves 2025), and the counting argument for this family (Green, Le Goues and
Brown 2026, in a solver synthesized per family). This entry combines them into one rewrite without family-specific code, adds certificates, and adds
the comparison under perturbation. Details: [docs/prior-art.md](docs/prior-art.md).

AI assistance: produced by an AI agent under the author's direction; see `entry.yaml`.
