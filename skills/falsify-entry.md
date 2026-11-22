# Falsify an entry

1. Clean checkout; run the entry's `reproduce` command; compare with the README.
2. Ablation: disable each component; record status and time per instance.
3. Sensitivity: at least 5 seeds or reorderings; at least 3 thread counts where threads apply.
4. Controls: inputs without the targeted structure; no answer may change; record added time.
5. Baseline search: look for a stronger public method; run it under the same budget.
6. Write results as files under `evidence/` and list every failed check in the entry's limits.
