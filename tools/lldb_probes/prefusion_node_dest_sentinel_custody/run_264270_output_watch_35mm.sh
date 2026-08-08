#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_264270_output_watch"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/output_watch_35mm.lldb" \
  > "$OUT/output_watch_35mm.log" 2>&1

python3 \
  "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py"
