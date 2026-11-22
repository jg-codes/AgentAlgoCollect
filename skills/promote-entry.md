# Promote an entry from working material

1. Copy only: method, tests, benchmark drivers, raw evidence, soundness notes, prior-work notes.
   Leave out working notes, decision logs and abandoned attempts.
2. Copy `templates/entry/entry.yaml` and fill every field. Set each gate criterion honestly.
3. Write the entry README in this order: problem, result table, method, reproduce, limits, prior work.
4. Write `bench/reproduce.sh`, run it from a clean checkout, and save its output under `evidence/`.
5. Run `python tools/gate.py`, `python tools/registry.py`, `ruff check .`, `pytest -q`.
6. Hand to the reviewer role before opening the pull request.
