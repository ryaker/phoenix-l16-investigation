#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/codex_final_output_hdr_writer_boundary"
RUN_DIR="$ROOT/runs/codex_final_output_hdr_writer_boundary"

mkdir -p "$RUN_DIR"

for focal in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE_DIR/hdr_writer_${focal}.lldb" \
    > "$RUN_DIR/hdr_writer_${focal}.log"
done
