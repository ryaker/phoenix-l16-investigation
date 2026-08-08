#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"
OUT="$ROOT/runs/prefusion_node_dest_20ca00_gate_custody_unit2"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_gate_unit2_${tier}.lldb" \
    "$ROOT/tools/lri_process" > "$OUT/node_dest_20ca00_gate_unit2_${tier}.log" 2>&1
done
