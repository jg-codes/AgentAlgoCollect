# Independent replays of published bound certificates

**Status: proposed** (track: theory; no result published yet)

Bounds for open constants are now found faster than they are checked. The public
[table of optimization constants](https://github.com/teorth/optimizationproblems) marks rows that
wait for an independent replay; this entry collects such replays.

A replay reads the certificate (for example the cell heights of a step function), computes the
claimed quantity in exact rational arithmetic with code written without reading the claimant's
verifier, and reports the exact value next to the printed one.

**The claim is refuted if** our checker and a claimant's verifier disagree and our checker is the
one that is wrong. Disagreements will be reported to the claimant before they appear here.

The first problem card is the [signed autoconvolution constant](../../../problems/extremal-math/signed-autoconvolution-constant.yaml).

Anyone may take this on: see [CONTRIBUTING.md](../../../CONTRIBUTING.md).
