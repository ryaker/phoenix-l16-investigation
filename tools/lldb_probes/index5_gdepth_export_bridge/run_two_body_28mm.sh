#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/index5_gdepth_export_bridge"
mkdir -p "$RUN_DIR"

for case_name in unit1_28mm unit2_28mm; do
  arch -x86_64 lldb -b \
    -s "$ROOT/tools/lldb_probes/index5_gdepth_export_bridge/${case_name}.lldb" \
    >"$RUN_DIR/${case_name}.log" 2>&1
done

python3 \
  "$ROOT/tools/lldb_probes/index5_gdepth_export_bridge/verify_gdepth_export_bridge.py"
