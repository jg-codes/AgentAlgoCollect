#!/usr/bin/env bash
# Generality / control instances used in runs/generality.txt and the solver matrix.
# The random families (randkcnf, tseitin, kclique gnp) were generated without a fixed
# seed, so regenerated files differ from the ones measured.
set -euo pipefail
mkdir -p gen
cnfgen -q php 13 12 > gen/php13.cnf
cnfgen -q op 40 > gen/op40.cnf
cnfgen -q randkcnf 3 200 1200 > gen/rand3_unsat.cnf
cnfgen -q randkcnf 3 300 1050 > gen/rand3_sat.cnf
cnfgen -q tseitin 50 4 > gen/tseitin50.cnf
cnfgen -q cliquecoloring 10 4 3 > gen/cc.cnf
cnfgen -q rphp 12 30 14 > gen/rphp_sat.cnf
cnfgen -q kclique 4 gnp 40 0.3 > gen/kclique.cnf
python3 -c "
import baselines
for fam, n, name in (('php', 9, 'gen/php9.cnf'), ('mchess', 14, 'gen/mchess14.cnf')):
    nv, alo, amo = baselines.FAMILIES[fam](n)
    top, cls = baselines.to_cnf(nv, alo, amo, 'pair')
    open(name, 'w').write(f'p cnf {top} {len(cls)}\n' + ''.join(' '.join(map(str, c)) + ' 0\n' for c in cls))
"
