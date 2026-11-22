# Protocol

An entry is a claim about an algorithm plus the material needed to check it. `tools/gate.py`
enforces the rules below on every pull request.

## Problem cards

A problem card states, with sources and a date: where the algorithm is used, the benchmarks and
their measures, the state of the art, and the remaining pain points. Every state-of-the-art item
needs a link, or a path in this repository if it was measured here. Every entry names one
problem card.

## Improvement dimensions

An entry lists what it improves, from a fixed list:

| Dimension | Typical measure |
|---|---|
| speed | time to solution; PAR-2 (average runtime, unsolved counted as twice the limit) |
| quality | objective value; gap to best known |
| robustness | results under perturbed inputs, seeds, orderings |
| generality | instance families covered without family-specific code |
| simplicity | same formulation and results with less code or fewer parameters |
| efficiency | memory, energy or hardware needed for the same result |
| verifiability | share of results with a checked proof or certificate |

A gain in one dimension is reported together with what it costs in the others.

## Criteria

| Criterion | Passes when |
|---|---|
| `soundness_tests` | Tests show the method is correct (for example equivalence checks, or a checker that rejects tampered certificates). |
| `public_baseline` | A named, strong public method was run under the same budget and hardware, with raw output in `evidence/`. Known alternatives that were not run are listed. |
| `one_command_reproduction` | One command reproduces the flagship result from a clean checkout. |
| `baseline_coverage` | Every known competing public method was run under the same protocol, or shown not to apply. |
| `real_benchmark_files` | The benchmark is an established public set, used with its original files (checksums recorded). |
| `second_machine` | The flagship result was rerun on different hardware. |
| `independent_reproduction` | Someone who is not an author reran it and is named in `entry.yaml`. |

A criterion that passes must point to evidence: one or more files inside the entry, or an https link. A criterion that does not pass must
carry a note saying why.

## Kinds of claim

Each claim in `entry.yaml` has a `kind`:

- `measured`: produced by running code, with raw output in `evidence/`.
- `machine-checked`: verified by a named checker or proof assistant. For a proof in Lean or a
  similar system, link the repository, commit and statement under `links.formal_proof`.
- `argued`: a written argument only.

The flagship result must be `measured` or `machine-checked`. An `argued` claim is welcome, is shown
as such in the registry, and is an open invitation to formalize or test it.

## Links

- `links.upstream`: where the improvement is offered to the original project (issue or pull
  request), with state `planned`, `open`, `merged` or `declined`. A declined offer stays listed.
- `links.formal_proof`: system, url, commit and the statement proved.

## Labels

- **proposed**: no result; a planned benchmark, a baseline and a `refuted_if` condition.
- **candidate**: the first three criteria pass.
- **confirmed**: all seven pass.
- **negative**: the first three pass and the result is that the idea does not improve on the baseline.

## Reporting rules

1. Numbers in an entry's README come from files in `evidence/`, through a script in the entry.
2. Every result names its baseline, budget and hardware.
3. Limits are listed in the entry README and in `entry.yaml`.
4. Prior work is cited; "not found in our search" is never written as "new".
5. AI assistance is stated in `entry.yaml`.
6. No entry imports code from another entry.

## Benchmark practice

- Fixed time limit, thread count and hardware, stated next to every result.
- For solver comparisons: instances solved within the limit and PAR-2. For optimization: gap to
  best known and time to reach it.
- At least 3 repeats for timings; report the median.
- Tune on one part of the benchmark and report on a part held out before tuning.
- Include inputs where the method should make no difference, and report the added cost there.

## Changing a label

Labels change only by pull request. Moving to **confirmed** needs the reproducer's name and their
run files in `evidence/`. If a result fails to reproduce, the entry is corrected or relabelled
**negative**, and the history stays.
