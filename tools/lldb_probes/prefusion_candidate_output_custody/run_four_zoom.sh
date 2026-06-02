#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/prefusion_candidate_output_custody"
RUN_DIR="$ROOT/runs/prefusion_candidate_output_custody"

mkdir -p "$RUN_DIR"

arch -x86_64 lldb -b -s "$PROBE_DIR/custody_28mm.lldb" > "$RUN_DIR/custody_28mm.log" 2>&1 &
pid_28=$!
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_35mm.lldb" > "$RUN_DIR/custody_35mm.log" 2>&1 &
pid_35=$!
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_70mm.lldb" > "$RUN_DIR/custody_70mm.log" 2>&1 &
pid_70=$!
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_150mm.lldb" > "$RUN_DIR/custody_150mm.log" 2>&1 &
pid_150=$!

wait "$pid_28"
wait "$pid_35"
wait "$pid_70"
wait "$pid_150"
