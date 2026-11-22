# Evaluators

An evaluator scores any candidate method for one problem card, automatically and reproducibly.

```bash
python evaluators/sat-pb/hidden_counting_in_clauses.py evaluators/sat-pb/baseline_candidate.py
```

Rules for an evaluator:

- The instance set is generated from fixed seeds inside the evaluator; no downloads.
- Every instance has a known answer, and satisfiable controls are included. A wrong answer on any
  instance sets `combined_score` to zero.
- It exposes `evaluate(program_path, **kwargs) -> dict` with a `combined_score`, and a command line
  that prints the same dict as JSON.
- It ships with a baseline candidate, so there is a starting point and a score to beat.

Attribution: giving every problem an automatic evaluator, and searching for better programs against
it, is the approach of AlphaEvolve (Novikov et al., 2025,
https://github.com/google-deepmind/alphaevolve_results). The `evaluate` interface matches the one
used by OpenEvolve (https://github.com/codelion/openevolve, Apache-2.0), an open implementation of
that approach, so these evaluators can be used there unchanged.
