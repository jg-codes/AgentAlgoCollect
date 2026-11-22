# AgentAlgoCollect

A public registry of algorithm improvements found with AI agents, where every entry states what it
shows, what it does not show, and how to check it.

**Purpose.** This is a place to collect and discuss results. It is research material, not
production-ready software: nothing here is hardened, supported or guaranteed to be fit for any use.

Contributions are welcome from people and from AI agents, as long as the improvement is benchmarked
and a named person stands behind it.

## Problems and entries

The registry has two layers:

- A **problem card** (`problems/<domain>/<problem>.yaml`) describes one problem: where the
  algorithm is used, the benchmarks and what they measure, the current state of the art with
  sources and dates, and what remains hard.
- An **entry** (`entries/<domain>/<entry>/`) is one attempt at a problem. It names its problem
  card, says which dimension it improves (speed, quality, robustness, generality, simplicity,
  efficiency, verifiability) and reports one flagship result against a named baseline.

## Labels

Each entry carries one label, enforced by a script in CI:

- **proposed**: an idea with a planned benchmark, a baseline and a stated way to refute it. No result yet.
- **candidate**: correct, fairly compared and reproducible with one command, with open criteria listed.
- **confirmed**: additionally every known competing method run, real benchmark files, a second
  machine, and a rerun by someone other than the author.
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

| Problem | Domain | Benchmark and measures | Open dimensions | Entries |
|---|---|---|---|---|
| [Refuting counting arguments hidden in clausal form](problems/sat-pb/hidden-counting-in-clauses.yaml) | sat-pb | GBD family relativized-pigeon-hole (55 instances): instances solved within the time limit; PAR-2 score; proof or certificate produced | robustness, generality, verifiability, speed | 2 |

### Results

| Entry | Status | Improves | Flagship result | Claims | Gate |
|---|---|---|---|---|---|
| [Counting where symmetry breaking fails: certified refutation of pigeonhole-type formulas](entries/sat-pb/cardinality-lifting/) | candidate | robustness, verifiability | Relativized pigeonhole, 15% of options forbidden at random (22 instances, 60 s): 22/22 refuted (max 2.01 s), all certified in a separate step vs BreakID + Kissat 4.0.4: 0/22 | 2 measured, 1 machine-checked, 2 argued | 3/7 |

### Open proposals (no result yet)

| Proposal | Domain | Planned benchmark | Refuted if |
|---|---|---|---|
| [Does the hidden conditional-counting pattern occur in real-world instances?](entries/sat-pb/product-extension-in-practice/) | sat-pb | Application tracks of recent SAT and pseudo-Boolean competitions; MIPLIB 0-1 models | The rule applies to under 1% of instances, or no instance changes outcome |
<!-- registry:end -->

"Claims" counts the claims of each kind; "Gate" counts the criteria an entry currently meets.
The rules are in [PROTOCOL.md](PROTOCOL.md).

## Layout

```
problems/<domain>/<problem>.yaml   problem card: use, benchmarks, state of the art, pain points
entries/<domain>/<entry>/          one self-contained folder per attempt
  entry.yaml                       problem card, claims, baseline, label, evidence paths
  README.md                        problem, result, method, reproduction, limits
  src/ tests/ bench/               method, tests, benchmark drivers
  evidence/                        raw run files and machine stamps
agents/  skills/                   role definitions and procedures for AI agents
tools/                             gate checker and registry generator
templates/                         starting points for a problem card and an entry
```

Domains so far: `sat-pb` (satisfiability and pseudo-Boolean solving),
`combinatorial-optimization`, `machine-learning`.

## Contributing

New entries, proposals, reproductions, formal proofs and corrections are welcome: see
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
