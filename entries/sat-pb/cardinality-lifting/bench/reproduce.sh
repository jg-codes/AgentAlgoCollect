#!/usr/bin/env bash
# Reproduces the flagship result: 22 symmetry-broken relativized pigeonhole instances,
# each refuted by the rewrite + Exact and certified by the independent checker.
# Needs: pip install exact cnfgen scipy.  Optional baseline: set KISSAT and BREAKID to the binaries.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/../work" && cd "$HERE/../work"
export PYTHONPATH="$HERE/../src:$HERE"
mkdir -p pert certs
python3 - <<'PY'
import gen_perturbed as g
for P, R in ((8, 25), (12, 36), (20, 20), (20, 60), (35, 35), (60, 60)):
    for seed in (1, 2):
        g.make(P, R, 0.15, seed)
for P, R in ((12, 36), (35, 35)):
    for seed in range(3, 8):
        g.make(P, R, 0.15, seed)
PY
total=0; ours=0; cert=0; base=0
for f in pert/*.cnf; do
  n=$(basename "$f" .cnf); total=$((total+1))
  st=$(python3 "$HERE/../src/cardlift.py" "$f" exact 60 | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
  [ "$st" = "UNSAT" ] && ours=$((ours+1))
  python3 "$HERE/../src/certify.py" "$f" "certs/$n.json" >/dev/null
  python3 "$HERE/../src/check_cert.py" "$f" "certs/$n.json" | grep -q '"verified": true' && cert=$((cert+1))
  if [ -n "${KISSAT:-}" ] && [ -n "${BREAKID:-}" ]; then
    b=$(timeout 60 bash -c "\"$BREAKID\" --verb 0 \"$f\" sb.cnf >/dev/null 2>&1 && \"$KISSAT\" -q sb.cnf" 2>/dev/null | grep -m1 '^s ' || true)
    [ "$b" = "s UNSATISFIABLE" ] && base=$((base+1))
  fi
done
echo "instances=$total refuted=$ours certified=$cert"
if [ -n "${KISSAT:-}" ] && [ -n "${BREAKID:-}" ]; then echo "breakid+kissat refuted=$base (60 s limit)"; fi
[ "$ours" = "$total" ] && [ "$cert" = "$total" ]
