#!/usr/bin/env bash
# usage: run_kissat.sh raw|breakid <timeout_s> <out.tsv>
mode=$1; T=$2; out=$3
K=${KISSAT:-kissat}
B=${BREAKID:-breakid}
cd "$(dirname "$0")/../work"
mkdir -p /tmp/bk
: > "$out"
for f in gbd_inst/*.cnf; do
  n=$(basename "$f" .cnf)
  s=$(date +%s.%N)
  if [ "$mode" = raw ]; then
    timeout "$T" "$K" -q "$f" >/tmp/bk/$n.out 2>&1; rc=$?
  else
    timeout "$T" bash -c "\"$B\" --verb 0 \"$f\" /tmp/bk/$n.sb.cnf >/dev/null 2>&1 && \"$K\" -q /tmp/bk/$n.sb.cnf" >/tmp/bk/$n.out 2>&1; rc=$?
    rm -f /tmp/bk/$n.sb.cnf
  fi
  e=$(date +%s.%N)
  st=$(grep -m1 '^s ' /tmp/bk/$n.out | cut -c3-); [ -z "$st" ] && st="TIMEOUT(rc=$rc)"
  printf '%s\t%s\t%.2f\n' "$n" "$st" "$(echo "$e - $s" | bc)" >> "$out"
done
echo done >> "$out.done"
