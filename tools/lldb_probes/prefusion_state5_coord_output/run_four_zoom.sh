#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/prefusion_state5_coord_output"
SCRIPT_DIR="$ROOT/tools/lldb_probes/prefusion_state5_coord_output"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$SCRIPT_DIR/state5_coord_output_28mm.lldb" > "$RUN_DIR/state5_coord_output_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/state5_coord_output_35mm.lldb" > "$RUN_DIR/state5_coord_output_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/state5_coord_output_70mm.lldb" > "$RUN_DIR/state5_coord_output_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/state5_coord_output_150mm.lldb" > "$RUN_DIR/state5_coord_output_150mm.log" 2>&1
