#!/bin/sh
set -eu

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PROBE="$ROOT/tools/lldb_probes/pipeline_linear_prophoto_stage"
OUT="$ROOT/runs/pipeline_linear_prophoto_stage"

mkdir -p "$OUT"
for tier in unit1_28mm unit1_35mm unit1_70mm unit1_150mm; do
  arch -x86_64 lldb -b -s "$PROBE/slot15_${tier}.lldb" >"$OUT/slot15_${tier}.log" 2>&1
done
python3 "$PROBE/verify_slot15_branch_incidence.py" --require unit1_28mm unit1_35mm unit1_70mm unit1_150mm
