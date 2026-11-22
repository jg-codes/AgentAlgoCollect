# Soundness of the pre-pass and the certificate

F is the input CNF over variables 1..n. All rules produce a system G over 1..n plus extension
variables, with F satisfiable iff G is satisfiable, and every model of F extends uniquely to a
model of G.

## Definitions (extension)
For literals x, y over F's variables, a fresh t gets the clauses (¬t ∨ x), (¬t ∨ y),
(t ∨ ¬x ∨ ¬y), i.e. t ↔ x ∧ y. Any assignment to 1..n extends by t := x ∧ y, so adding
definitions is a conservative extension (extended resolution).

## R1 product extension
A clause (a ∨ b ∨ c ∨ d) equals ¬(¬a ∧ ¬b) ∨ ¬(¬c ∧ ¬d). With t1 ↔ ¬a ∧ ¬b and
t2 ↔ ¬c ∧ ¬d it is equivalent to (¬t1 ∨ ¬t2) under the definitions. The pairing is chosen
to maximise the minimum recurrence of the two pairs across all 4-clauses; a pairing is
used only if both pairs recur at least twice.

## R2 substitution
Let C contain ¬x and y, with t ↔ x ∧ y defined. If x is false, C is satisfied by ¬x before
and after replacing y by t. If x is true, t = y. So C and C[y := t] agree under the
definitions. Binary clauses are skipped, which is safe.

## R3 literal cliques
A binary clause (a ∨ b) forbids ¬a and ¬b both true: an edge between them. For a clique
K in this literal graph, every pair in K is forbidden, so Σ_{ℓ∈K} ℓ ≤ 1 is implied
(the converse also holds, so the covered binary clauses can be deleted). Cliques can
contain negated literals; a clique {p_1..p_m, ¬r} gives Σ p_i + (1 − r) ≤ 1, i.e.
Σ p_i ≤ r.

## Certificate
check_cert.py accepts a lifted constraint only if it is (a) a clause of F, (b) a definition
clause, (c) an R1 binary whose expansion is a clause of F, (d) an R2 clause whose reverse
substitution is a clause of F, or (e) an AMO all of whose pairs are backed by (a)–(c).
It then checks exact rational multipliers y ≥ 0 whose combination c·x ≥ d has
Σ max(c_j, 0) < d, so no x ∈ [0,1]^N satisfies it. Hence G is infeasible even over the
reals, so G and therefore F are unsatisfiable. The checker shares no code with the pre-pass.

## Why RPHP becomes LP-infeasible (P pigeons, R places, H = P − 1 holes)
Summing the P pigeon clauses and the R clique constraints Σ_u p_uv ≤ r_v gives Σ r ≥ P.
The R2-rewritten clauses r_v → ∨_k t_vk give Σ t ≥ Σ r. The H hole cliques give
Σ t ≤ H = P − 1. All multipliers are 1, and the contradiction is P ≤ P − 1. Forbidding options adds unit clauses and leaves every clause used above in place, so the same
certificate still applies. This argument assumes the pairing rule and the greedy clique cover find
the pairs and cliques named above; that is observed on all tested instances, not proved.
