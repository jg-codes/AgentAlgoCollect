# Prior art (screened 2026-11-20/21, shallow: web search plus the papers below)

| Work | What it does | Relation |
|---|---|---|
| Haken 1985 | PHP needs exponential-size resolution refutations | Why CDCL fails on PHP |
| Cook, Coullard, Turán 1987; Hooker 1988 | Cutting planes p-simulates resolution, linear-size PHP proofs | Why lifting to cardinality helps |
| Biere, Le Berre, Lonca, Manthey 2014 | Detect cardinality constraints in CNF | Same idea as R3 (detection), without deletion |
| Elffers & Nordström, AAAI 2020 (doi:10.1609/aaai.v34i02.5508) | On-the-fly cardinality detection in RoundingSat; pairwise PHP 14/14; names relativized PHP as a known failure | Closest PB-solver work; RPHP is the case they could not handle |
| Reeves, PhD thesis CMU 2025 | Cardinality reasoning in CDCL; removes binaries implied by an extracted AtMostOne | Same deletion step, in a CDCL setting |
| Green, Le Goues, Brown, arXiv 2609.14836 (2026) | Hyperspecialized per-family solvers; RPHP specialist uses extension variables and "pseudo-Boolean clique counting"; 9/11 validation vs baseline 8/11 | Same counting argument, synthesized per family; ours is family-agnostic and certificate-producing |
| BreakID (Devriendt et al.); SATSUMA (arXiv 2511.16637) | Symmetry breaking; makes RPHP easy for CDCL | Strongest baseline here; loses once symmetry is broken |
| Manthey, Heule, Biere 2012 (BVA); SBVA 2023 | Structured variable addition / reencoding | Related to rule 1; SBVA not run |
| GBD family relativized-pigeon-hole (benchmark-database.de) | 55 instances, 14 listed unknown | Benchmark; instances regenerated with CNFgen from the file names, not hash-matched |

Not found in the screen: a family-agnostic pre-pass that makes RPHP LP-infeasible and emits a
checkable Farkas certificate. Absence in a shallow screen is not evidence of novelty; this entry is described as a
combination of known parts.
