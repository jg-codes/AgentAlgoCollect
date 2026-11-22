# Contributing

Benchmarked improvements found with AI agents are welcome here. So are improvements found by hand,
engineering fixes that make a known algorithm faster, leaner or simpler, benchmarks, ideas that
still need testing, and results that did not work out.

## Ways to contribute

1. **Reproduce an entry.** Run its `reproduce` command on your machine and open a pull request
   that adds your output and machine details under `evidence/`. This is what confirms an entry.
2. **Add a result.** Open an "Entry proposal" issue first: the problem, the baseline and the
   benchmark. Then copy `templates/entry/` to `entries/<domain>/<your-entry>/` and open a pull request.
3. **Add a benchmark.** Benchmarks are wanted: public suites, instance sets published with papers,
   generators, and your own where none exists. Copy `templates/benchmark/` to
   `benchmarks/<domain>/`. Only add what you have checked; give the link and the date.
4. **Add or update a problem card.** Describe a problem (use, benchmarks, state of the art with
   sources, pain points) from `templates/problem/`, or correct an outdated one.
5. **Take on a challenge.** Where a problem card has an evaluator, run your method or your agent
   against it (`python evaluators/<domain>/<name>.py your_candidate.py`) and submit the result as
   an entry. Evaluators for other problem cards are welcome too.
6. **Add a proposal.** An idea without results can be entered with the label `proposed`, if it
   names a benchmark, a baseline and what would refute it. Anyone may pick up an open proposal.
7. **Strengthen a claim.** Turn an `argued` claim into a `machine-checked` one, for example with a
   Lean proof, or into a `measured` one with a test. Link the proof repository and commit.
8. **Carry it upstream.** If you open an issue or pull request in the original project, add it
   under `links.upstream` with its state.
9. **Report an error.** If a number, a claim or a citation is wrong, open an issue or a pull request.

## Contributions made with AI agents

- A named person submits the contribution and answers for it.
- `ai_assistance` in `entry.yaml` says what the agent did and what a person checked.
- The same gate applies to everyone. An agent's fluent write-up is not evidence; run files are.
- `agents/` and `skills/` hold the role definitions and procedures used for the existing entries.
  You can point your own agent at them.

## Rules for a new entry

- One entry per pull request, in one folder. Choose an existing domain folder; propose a new
  domain in the issue if none fits.
- Choose the track: `theory`, `applied` or `engineering`. Each has its own criteria.
- New entries start as **proposed**, **candidate** or **negative**. See [PROTOCOL.md](PROTOCOL.md).
- Mark every claim as `measured`, `machine-checked` or `argued`.
- Name the problem card and the dimensions the entry improves; report what the gain costs elsewhere.
- `python tools/scan_sensitive.py`, `python tools/gate.py`, `python tools/registry.py --check`,
  `ruff check .` and `pytest -q` pass.
- Keep `evidence/` small (raw result files, not benchmark instances). Fetch or generate large
  files by script and record checksums.
- State AI assistance in `entry.yaml`. Entries written with AI agents are welcome; unverified
  claims are not.
- Cite prior work, including work that reduces the novelty of your result.

## Privacy and secrets

Nothing that identifies a person or a machine belongs in this repository: host names, user names,
home paths, network addresses, serial numbers, e-mail addresses, keys or tokens. Benchmarks need
the hardware class, so record it with `python tools/stamp.py`, which leaves identity out.
`tools/scan_sensitive.py` blocks such data at commit time (`pre-commit install`) and on every pull
request. It reports findings and does not rewrite files, so that evidence is never changed silently.

## Review

A maintainer checks each pull request against the checklist in the pull request template: the
flagship number is traced from the README to the evidence file, the baseline is a strong public
method with the alternatives listed, the reproduction command is run, and the wording claims no more than the evidence shows.

## License and sign-off

Code contributions are accepted under Apache-2.0, text and data under CC BY 4.0 (see `NOTICE`).
Sign your commits (`git commit -s`) to certify you have the right to submit them (Developer
Certificate of Origin). Contributors are credited in the entries they author or reproduce.

This repository is for collecting and discussing results. Nothing in it is production-ready.
