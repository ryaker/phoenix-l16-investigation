#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/prefusion_record_state_gate_histogram"
RUN_DIR="$ROOT/runs/prefusion_record_state_gate_histogram"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$PROBE_DIR/custody_state_28mm.lldb" > "$RUN_DIR/custody_state_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_state_35mm.lldb" > "$RUN_DIR/custody_state_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_state_70mm.lldb" > "$RUN_DIR/custody_state_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_state_150mm.lldb" > "$RUN_DIR/custody_state_150mm.log" 2>&1
