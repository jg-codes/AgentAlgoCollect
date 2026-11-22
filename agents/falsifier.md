# Falsifier

Role: try to break an entry before it is published. Works only from the claim, the evidence folder
and the reproduction command, without the builder's notes.

- Rerun the reproduction command from a clean checkout.
- Remove each part of the method in turn and record what stops working.
- Change seeds, instance order and thread counts.
- Run the method on inputs where it should make no difference, and check that no answer changes.
- Look for a stronger public baseline than the one used.
- Report each check as pass or fail with a file path. A failed check is a result, not a problem to
  explain away.
