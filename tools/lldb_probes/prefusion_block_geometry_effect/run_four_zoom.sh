#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
RUN_DIR="$ROOT/runs/prefusion_block_geometry_effect"
SCRIPT_DIR="$ROOT/tools/lldb_probes/prefusion_block_geometry_effect"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$SCRIPT_DIR/block_geometry_effect_28mm.lldb" > "$RUN_DIR/block_geometry_effect_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/block_geometry_effect_35mm.lldb" > "$RUN_DIR/block_geometry_effect_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/block_geometry_effect_70mm.lldb" > "$RUN_DIR/block_geometry_effect_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/block_geometry_effect_150mm.lldb" > "$RUN_DIR/block_geometry_effect_150mm.log" 2>&1
