# Governance

## Roles

- **Maintainer:** Johannes Gast (@jg-codes). Merges pull requests and decides labels.
- **Contributors:** anyone who opens an issue or pull request.
- **Reproducers:** contributors who rerun an entry. They are named in the entry they confirm.

More maintainers can be added once there are regular contributors; a domain folder can then get its
own reviewer through `.github/CODEOWNERS`.

## Decisions

- Labels are decided by the rules in `PROTOCOL.md`, checked by `tools/gate.py`. The maintainer cannot
  grant a label the script rejects.
- Changes to `PROTOCOL.md` or `tools/gate.py` are made by pull request with a stated reason, and never
  in the same pull request as an entry that benefits from them.
- A maintainer does not confirm an entry they authored. Confirmation needs another person's rerun.

## Corrections

- Anyone can report an error. Confirmed errors are fixed in the entry and noted in its README
  under "Corrections", with the date.
- If a result does not reproduce, the entry is relabelled, not deleted.

## Conflicts of interest

Authors state any affiliation relevant to an entry (for example with a solver or a benchmark) in
the entry README.

## Releases

Tagged releases are archived on Zenodo. An entry's version in `entry.yaml` changes whenever its
result, evidence or label changes.
