#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"
GENERIC_OUT="$ROOT/runs/prefusion_node_dest_20ca00_gate_custody_unit2"
TARGET_OUT="$ROOT/runs/prefusion_node_dest_20ca00_gate_target_custody_unit2"
mkdir -p "$GENERIC_OUT" "$TARGET_OUT"

# One wide anchor, the observed cross-unit-divergent wide crop, and one tele anchor.
arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_gate_unit2_28mm.lldb" \
  "$ROOT/tools/lri_process" > "$GENERIC_OUT/node_dest_20ca00_gate_unit2_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_gate_unit2_35mm.lldb" \
  "$ROOT/tools/lri_process" > "$GENERIC_OUT/node_dest_20ca00_gate_unit2_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_gate_unit2_target_35mm.lldb" \
  "$ROOT/tools/lri_process" > "$TARGET_OUT/node_dest_20ca00_gate_unit2_target_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_gate_unit2_70mm.lldb" \
  "$ROOT/tools/lri_process" > "$GENERIC_OUT/node_dest_20ca00_gate_unit2_70mm.log" 2>&1

python3 "$PROBE/verify_node_dest_20ca00_gate_crossunit_selected.py"
