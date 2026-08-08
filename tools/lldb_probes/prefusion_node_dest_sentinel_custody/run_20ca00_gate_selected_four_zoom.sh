#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
GENERIC_OUT="$ROOT/runs/prefusion_node_dest_20ca00_gate_custody"
TARGET_OUT="$ROOT/runs/prefusion_node_dest_20ca00_gate_target_custody"
mkdir -p "$GENERIC_OUT" "$TARGET_OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_28mm.lldb" "$ROOT/tools/lri_process" > "$TARGET_OUT/node_dest_20ca00_gate_target_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_35mm.lldb" "$ROOT/tools/lri_process" > "$TARGET_OUT/node_dest_20ca00_gate_target_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_70mm.lldb" "$ROOT/tools/lri_process" > "$GENERIC_OUT/node_dest_20ca00_gate_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_150mm.lldb" "$ROOT/tools/lri_process" > "$TARGET_OUT/node_dest_20ca00_gate_target_150mm.log" 2>&1

python3 "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_gate_selected_custody.py"
