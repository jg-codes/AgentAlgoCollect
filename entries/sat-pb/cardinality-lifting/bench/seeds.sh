#!/usr/bin/env bash
B=${BREAKID:-breakid}; K=${KISSAT:-kissat}
cd "$(dirname "$0")/../work"; out=runs/seeds.tsv; : > $out
for f in pert/*_s[3-7].cnf reshuf/*.cnf; do
  n=$(basename $f .cnf); s=$(date +%s.%N)
  st=$(timeout 60 bash -c "$B --verb 0 $f /tmp/sd.cnf >/dev/null 2>&1 && $K -q /tmp/sd.cnf" 2>/dev/null | grep -m1 '^s' | cut -c3-); [ -z "$st" ] && st=TIMEOUT
  bt=$(echo "$(date +%s.%N)-$s" | bc)
  o=$(python3 -c "import fals,json;r=fals.one('$f','123','exact',60);print(r['status'],r['total_s'])")
  python3 ../src/certify.py $f certs/$n.json >/dev/null; c=$(python3 ../src/check_cert.py $f certs/$n.json | grep -o '"verified": [a-z]*' | cut -d' ' -f2)
  printf '%s\t%s\t%.2f\t%s\t%s\n' "$n" "$st" "$bt" "$o" "$c" >> $out
done
echo done > runs/seeds.done
