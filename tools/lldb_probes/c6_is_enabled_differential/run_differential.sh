#!/bin/sh
set -eu

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PROBE="$ROOT/tools/lldb_probes/c6_is_enabled_differential"
OUT="$ROOT/runs/c6_is_enabled_differential"

mkdir -p "$OUT"
for tier in 70mm 150mm; do
  for condition in baseline forced; do
    for repeat in 1 2; do
      script="$PROBE/${tier}_${condition}_${repeat}.lldb"
      log="$OUT/${tier}_${condition}_${repeat}.log"
      arch -x86_64 lldb -b -s "$script" >"$log" 2>&1
    done
  done
done

python3 "$PROBE/verify_c6_is_enabled_differential.py"
