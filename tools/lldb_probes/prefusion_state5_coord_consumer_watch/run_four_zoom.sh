#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/prefusion_state5_coord_consumer_watch"
SCRIPT_DIR="$ROOT/tools/lldb_probes/prefusion_state5_coord_consumer_watch"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$SCRIPT_DIR/coord_consumer_watch_28mm.lldb" > "$RUN_DIR/coord_consumer_watch_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/coord_consumer_watch_35mm.lldb" > "$RUN_DIR/coord_consumer_watch_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/coord_consumer_watch_70mm.lldb" > "$RUN_DIR/coord_consumer_watch_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$SCRIPT_DIR/coord_consumer_watch_150mm.lldb" > "$RUN_DIR/coord_consumer_watch_150mm.log" 2>&1
