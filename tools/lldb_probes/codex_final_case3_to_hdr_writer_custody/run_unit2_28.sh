#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/codex_final_case3_to_hdr_writer_custody"
RUN_DIR="$ROOT/runs/codex_final_case3_to_hdr_writer_custody"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$PROBE_DIR/case3_writer_unit2_28mm.lldb" \
  > "$RUN_DIR/case3_writer_unit2_28mm.log"
