#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"
OUT="$ROOT/runs/prefusion_20ca00_record_z_watch"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$PROBE/node_dest_20ca00_record_z_watch_unit1_70mm.lldb" \
  "$ROOT/tools/lri_process" > "$OUT/record_z_watch_unit1_70mm.log" 2>&1
