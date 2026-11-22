# Instructions for AI agents working in this repository

Read `PROTOCOL.md` first. It defines what an entry may claim.

## Roles and procedures

- `agents/builder.md`, `agents/falsifier.md`, `agents/reviewer.md`: who does what. The falsifier and
  the reviewer work from the entry alone, without the builder's notes.
- `skills/promote-entry.md`, `skills/falsify-entry.md`, `skills/review-entry.md`,
  `skills/sanitize-evidence.md`: step-by-step procedures.

## Rules

1. Never write a number by hand. Numbers come from files in `evidence/` through a script.
2. Never raise a label or tick a gate criterion without the evidence file it points to.
3. Mark every claim `measured`, `machine-checked` or `argued`. Do not present an argument as a result.
4. Cite prior work, including work that makes the result less new.
5. Before every commit run: `python tools/scan_sensitive.py`, `python tools/gate.py`,
   `python tools/registry.py --check`, `ruff check .`, `pytest -q`.
6. Nothing that identifies a person or a machine goes into the repository: no host names, user
   names, home paths, addresses, serial numbers, e-mail addresses, keys or tokens. Record hardware
   with `python tools/stamp.py` only.
7. Do not copy working notes, decision logs or abandoned attempts into an entry.
8. A person submits and answers for every contribution. State what you did under `ai_assistance`.
9. Do not open issues or pull requests in other projects on your own. Prepare the text and leave
   posting to the person responsible.
