"""RPHP with random forbidden options (still UNSAT: only removes choices), then shuffled.
Breaks the pigeon/resting-place/hole symmetries that symmetry breakers exploit."""

import os
import random
import subprocess


def make(P, R, frac, seed):
    H = P - 1
    raw = subprocess.run(
        ["cnfgen", "-q", "rphp", str(P), str(R), str(H)], capture_output=True, text=True, check=True
    ).stdout
    lines = [lit for lit in raw.splitlines() if lit and lit[0] not in "cp"]
    rng = random.Random(seed)
    npv, nqv = P * R, R * H
    units = [-v for v in range(1, npv + 1) if rng.random() < frac]
    units += [-(npv + v) for v in range(1, nqv + 1) if rng.random() < frac]
    nv = npv + nqv + R
    name = f"pert/rphp_pert_p{P}_r{R}_f{int(frac * 100)}_s{seed}"
    with open(name + ".raw.cnf", "w") as f:
        f.write(f"p cnf {nv} {len(lines) + len(units)}\n" + "\n".join(lines) + "\n")
        f.write("\n".join(f"{u} 0" for u in units) + "\n")
    subprocess.run(["cnfshuffle", "-i", name + ".raw.cnf", "-o", name + ".cnf"], check=True)
    os.remove(name + ".raw.cnf")
    return name + ".cnf", len(units)


if __name__ == "__main__":
    os.makedirs("pert", exist_ok=True)
    for P, R in ((8, 25), (12, 36), (20, 20), (20, 60), (35, 35), (60, 60)):
        for seed in (1, 2):
            print(make(P, R, 0.15, seed))
