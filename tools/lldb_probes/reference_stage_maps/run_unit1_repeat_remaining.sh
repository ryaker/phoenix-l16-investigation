#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
for focal in 35 70 150; do
  OUT="$ROOT/runs/reference_stage_maps/unit1_${focal}mm_repeat"
  mkdir -p "$OUT"
  arch -x86_64 lldb -s \
    "$ROOT/tools/lldb_probes/reference_stage_maps/unit1_${focal}mm_repeat.lldb" \
    > "$OUT/run.log" 2>&1
done

python3 "$ROOT/tools/lldb_probes/reference_stage_maps/analyze_reference_stage_maps.py"
