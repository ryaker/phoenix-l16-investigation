#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"
OUT="$ROOT/runs/prefusion_20ca00_solve_output_only"
mkdir -p "$OUT"

run_probe() {
  local stem="$1"
  local script="$2"
  arch -x86_64 lldb -b -s "$PROBE/$script" \
    "$ROOT/tools/lri_process" > "$OUT/$stem.log" 2>&1
}

run_probe "prefusion_20ca00_solve_output_only_unit1_70mm" \
  "node_dest_20ca00_solve_output_only_unit1_70mm.lldb"
run_probe "prefusion_20ca00_solve_output_only_unit2_35mm" \
  "node_dest_20ca00_solve_output_only_unit2_35mm.lldb"
