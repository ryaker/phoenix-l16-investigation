#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/prefusion_node_sentinel_write"
SCRIPT_DIR="$ROOT/tools/lldb_probes/prefusion_node_sentinel_write"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$SCRIPT_DIR/node_sentinel_write_28mm.lldb" > "$RUN_DIR/node_sentinel_write_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/node_sentinel_write_35mm.lldb" > "$RUN_DIR/node_sentinel_write_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/node_sentinel_write_70mm.lldb" > "$RUN_DIR/node_sentinel_write_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/node_sentinel_write_150mm.lldb" > "$RUN_DIR/node_sentinel_write_150mm.log" 2>&1
