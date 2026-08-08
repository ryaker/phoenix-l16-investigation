#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/prefusion_block_decision_cascade"
BIN="$ROOT/tools/lri_process"

mkdir -p "$ROOT/runs/prefusion_block_decision_cascade"

for zoom in 28mm 35mm 70mm 150mm; do
  echo "== prefusion_block_decision_cascade ${zoom} =="
  arch -x86_64 lldb -b -s "$PROBE_DIR/block_decision_cascade_${zoom}.lldb" "$BIN"
done
