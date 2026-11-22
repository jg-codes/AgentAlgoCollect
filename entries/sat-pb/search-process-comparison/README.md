# Evolutionary code search against a role-separated agent workflow

**Status: proposed** (track: applied; no result yet)

Both approaches would start from the same baseline candidate (score 8 of 15 on the problem card's
evaluator) and get the same language model and token budget. The outcome is the evaluator score on
fresh seeds that neither search has seen, over three runs per approach.

**The claim is refuted if** evolutionary search reaches an equal or higher score in at least two of
three runs. Either outcome will be published here.

Note: the existing [cardinality-lifting](../cardinality-lifting/) entry does not count as evidence
for this claim. It was developed with human steering and without a budget cap.

Anyone may take this on: see [CONTRIBUTING.md](../../../CONTRIBUTING.md).
