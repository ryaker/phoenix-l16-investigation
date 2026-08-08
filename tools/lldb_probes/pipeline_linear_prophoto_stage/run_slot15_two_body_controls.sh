#!/bin/sh
set -eu

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PROBE="$ROOT/tools/lldb_probes/pipeline_linear_prophoto_stage"
OUT="$ROOT/runs/pipeline_linear_prophoto_stage"

mkdir -p "$OUT"
arch -x86_64 lldb -b -s "$PROBE/slot15_unit2_28mm.lldb" >"$OUT/slot15_unit2_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE/slot15_unit2_70mm_sample.lldb" >"$OUT/slot15_unit2_70mm_sample.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE/slot15_unit2_70mm.lldb" >"$OUT/slot15_unit2_70mm.log" 2>&1
python3 "$PROBE/verify_slot15_branch_incidence.py" \
  --require unit1_28mm unit1_70mm unit2_28mm \
  --require-zero unit2_70mm \
  --require-sample unit2_70mm
