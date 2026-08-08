#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"
OUT="$ROOT/runs/prefusion_216f60_score_vector_consumer"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$PROBE/node_dest_216f60_score_vector_consumer_unit1_70mm.lldb" \
  "$ROOT/tools/lri_process" > "$OUT/score_vector_consumer_unit1_70mm.log" 2>&1
