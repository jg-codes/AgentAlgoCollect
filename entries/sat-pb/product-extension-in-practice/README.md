# Does the hidden conditional-counting pattern occur in real-world instances?

**Status: proposed** (track: applied; no result yet)

The [cardinality-lifting](../cardinality-lifting/) entry shows a rewrite that helps on crafted
formulas. This proposal asks whether its key rule ever applies outside them.

**Plan.** Run the detector over application-track instances of recent SAT and pseudo-Boolean
competitions and over 0-1 models from MIPLIB. Count the instances where the product-extension rule
applies, then compare each solver on the original and the rewritten instance under the same budget.

**The claim is refuted if** the rule applies to under 1% of instances, or no instance changes outcome.
A refutation would be published here as a negative entry.

Anyone may take this on: see [CONTRIBUTING.md](../../../CONTRIBUTING.md).
