#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/codex_final_compositing_case1_case3_boundary"
RUN_DIR="$ROOT/runs/codex_final_compositing_case1_case3_boundary"

mkdir -p "$RUN_DIR"

for focal in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE_DIR/case1_case3_${focal}.lldb" \
    > "$RUN_DIR/case1_case3_${focal}.log"
done
