# AgentAlgoCollect

A public registry of algorithm improvements found with AI agents, where every entry states what it
shows, what it does not show, and how to check it.

**Purpose.** This is a place to collect and discuss results. It is research material, not
production-ready software: nothing here is hardened, supported or guaranteed to be fit for any use.

Contributions are welcome from people and from AI agents, as long as the improvement is benchmarked
and a named person stands behind it.

## Three tracks

| Track | For | Evidence expected |
|---|---|---|
| **theory** | Algorithms and analyses that cannot be run or benchmarked today, for example quantum or asymptotic results | A written argument; ideally a machine-checked proof |
| **applied** | New or changed algorithms that run today | A benchmark comparison against a public baseline |
| **engineering** | The same algorithm made more useful: faster, leaner, simpler, or better fitted to its data and hardware | Proof that behaviour is unchanged, plus measurements on stated hardware, software and data |

Engineering improvements are as welcome as new algorithms. Much practical progress comes from using
resources better. Each track has its own gate criteria (see [PROTOCOL.md](PROTOCOL.md)). An entry
keeps its folder when it moves track, for example when a theoretical method becomes runnable.

## Problems, benchmarks and entries

The registry has three layers:

- A **benchmark card** (`benchmarks/<domain>/<benchmark>.yaml`) describes one benchmark: where to
  get it, what it measures and under which protocol. Where no public benchmark exists, an entry can
  publish its own with a generator; it is listed as `own` until others adopt it.

- A **problem card** (`problems/<domain>/<problem>.yaml`) describes one problem: where the
  algorithm is used, which benchmarks apply, the current state of the art with sources and dates,
  and what remains hard.
- An **entry** (`entries/<domain>/<entry>/`) is one attempt at a problem. It names its track,
  its problem card and its benchmark, says which dimension it improves (speed, quality, robustness, generality, simplicity,
  efficiency, verifiability) and reports one flagship result against a named baseline.

## Labels

Each entry carries one label, enforced by a script in CI:

- **proposed**: an idea with a planned benchmark, a baseline and a stated way to refute it. No result yet.
- **candidate**: meets the minimum criteria of its track, with the open ones listed.
- **confirmed**: meets every criterion of its track, including a check by someone other than the author.
- **negative**: an idea that was tested properly and did not work. These are kept on purpose.

## How each claim is backed

Every claim inside an entry says which of three kinds it is:

| Kind | Meaning |
|---|---|
| measured | Produced by running code; the raw output is in the entry's `evidence/` folder. |
| machine-checked | Verified by a checker or proof assistant (for example a certificate checker or Lean); the checker is named. |
| argued | Supported by a written argument only. Not yet run or formally proved. |

A flagship result must be measured or machine-checked. Entries can link to a formal proof
(repository, commit, statement) and to the upstream issue or pull request where the improvement
is offered to the original project.

## Registry

<!-- registry:start -->
### Problems

| Problem | Domain | Benchmarks | Open dimensions | Entries |
|---|---|---|---|---|
| [Refuting counting arguments hidden in clausal form](problems/sat-pb/hidden-counting-in-clauses.yaml) | sat-pb | gbd-relativized-pigeon-hole, perturbed-relativized-pigeonhole, pb-competition-2025 | robustness, generality, verifiability, speed | 2 |

### Benchmarks

| Benchmark | Domain | Kind | Measures | Protocol |
|---|---|---|---|---|
| [MIPLIB 2017](benchmarks/combinatorial-optimization/miplib-2017.yaml) | combinatorial-optimization | public-suite | instances solved within the time limit; time to optimality; gap to best known | Instances are tagged easy (solved within one hour by an out-of-the-box solver), hard or open. |
| [OR-Library](benchmarks/combinatorial-optimization/or-library.yaml) | combinatorial-optimization | public-suite | objective value; gap to best known; time to best solution | None fixed by the library; state limits, hardware and the best-known values used. |
| [kvpress evaluation suite and leaderboard](benchmarks/machine-learning/kvpress-evaluation.yaml) | machine-learning | public-suite | task accuracy at a given compression ratio; peak memory; total time | See evaluation/README.md in the repository; state model, dataset, context length and compression ratio. |
| [GBD family relativized-pigeon-hole](benchmarks/sat-pb/gbd-relativized-pigeon-hole.yaml) | sat-pb | public-suite | instances solved within the time limit; PAR-2 score; proof or certificate produced | Per the SAT Competition year the instances come from; state the limit used. |
| [Pseudo-Boolean Competition 2025](benchmarks/sat-pb/pb-competition-2025.yaml) | sat-pb | public-suite | instances solved within the time limit; certificate validated by VeriPB | Sequential solvers: 1 h CPU time and 31 GB RAM per job. Certificates in VeriPB format. |
| [Relativized pigeonhole with forbidden options](benchmarks/sat-pb/perturbed-relativized-pigeonhole.yaml) | sat-pb | own | instances refuted within the time limit; certificate verified | 60 s per instance in the first use; 15% of pigeon-place and place-hole options forbidden, clause order shuffled. |
| [SAT Competition 2025](benchmarks/sat-pb/sat-competition-2025.yaml) | sat-pb | public-suite | instances solved within the time limit; PAR-2 score | Limits and scoring are set in the competition rules; state the ones used. |

### Results: theory

No entries yet.

### Results: applied

| Entry | Status | Improves | Flagship result | Claims | Gate |
|---|---|---|---|---|---|
| [Counting where symmetry breaking fails: certified refutation of pigeonhole-type formulas](entries/sat-pb/cardinality-lifting/) | candidate | robustness, verifiability | Relativized pigeonhole, 15% of options forbidden at random (22 instances, 60 s): 22/22 refuted (max 2.01 s), all certified in a separate step vs BreakID + Kissat 4.0.4: 0/22 | 2 measured, 1 machine-checked, 2 argued | 3/7 |

### Results: engineering

No entries yet.

### Open proposals (no result yet)

| Proposal | Track | Planned benchmark | Refuted if |
|---|---|---|---|
| [Does the hidden conditional-counting pattern occur in real-world instances?](entries/sat-pb/product-extension-in-practice/) | applied | Application tracks of recent SAT and pseudo-Boolean competitions; MIPLIB 0-1 models | The rule applies to under 1% of instances, or no instance changes outcome |
<!-- registry:end -->

"Claims" counts the claims of each kind; "Gate" counts the criteria an entry currently meets.
The rules are in [PROTOCOL.md](PROTOCOL.md).

## Layout

```
benchmarks/<domain>/<name>.yaml    benchmark card: source, measures, protocol, access
problems/<domain>/<problem>.yaml   problem card: use, benchmarks, state of the art, pain points
entries/<domain>/<entry>/          one self-contained folder per attempt
  entry.yaml                       problem card, claims, baseline, label, evidence paths
  README.md                        problem, result, method, reproduction, limits
  src/ tests/ bench/               method, tests, benchmark drivers
  evidence/                        raw run files and machine stamps
agents/  skills/                   role definitions and procedures for AI agents
tools/                             gate checker and registry generator
templates/                         starting points for benchmark cards, problem cards and entries
```

Domains so far: `sat-pb` (satisfiability and pseudo-Boolean solving),
`combinatorial-optimization`, `machine-learning`.

## Contributing

New entries, engineering improvements, benchmarks, proposals, reproductions, formal proofs and
corrections are welcome: see
[CONTRIBUTING.md](CONTRIBUTING.md). How decisions are made: [GOVERNANCE.md](GOVERNANCE.md). A rerun of an existing entry on your own machine is the most
useful contribution, because it is what moves an entry from candidate to confirmed.

## License and citing

Permissive, with attribution required. Code is under Apache-2.0; redistributions must keep the
`NOTICE` file. Text, problem cards, tables and evidence are under CC BY 4.0; reuse must credit
this repository. To cite, see `CITATION.cff`; releases are archived on Zenodo.

## AI assistance

Entries are produced with AI agents under human direction and say so in `entry.yaml`. The agents'
role definitions and procedures are in `agents/` and `skills/`, so the same protocol can be run on
other algorithms.
