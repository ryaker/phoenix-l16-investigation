#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/index5_gdepth_export_bridge"
mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/index5_gdepth_export_bridge/unit1_28mm.lldb" \
  >"$RUN_DIR/unit1_28mm.log" 2>&1
