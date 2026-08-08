#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_state5_coord_node_dest_watch"

mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.lldb" \
  > "$OUT/node_dest_watch_unit2_28mm.log" 2>&1
