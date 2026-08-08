#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_src2_source_camera_identity"
OUT="$ROOT/runs/prefusion_src2_source_camera_identity"
mkdir -p "$OUT"

for case_name in unit1_28mm unit1_70mm unit2_28mm unit2_70mm; do
  arch -x86_64 lldb -b -s "$PROBE/src2_source_camera_${case_name}.lldb" \
    > "$OUT/${case_name}.log"
done
