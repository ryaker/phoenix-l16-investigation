#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/lri_firing_set_census"
RUN_DIR="$ROOT/runs/lri_firing_set_census"

mkdir -p "$RUN_DIR"
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_28mm_tele_unit1.lldb" > "$RUN_DIR/custody_28mm_tele_unit1.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_28mm_tele_unit2.lldb" > "$RUN_DIR/custody_28mm_tele_unit2.log" 2>&1
arch -x86_64 lldb -b -s "$PROBE_DIR/custody_74mm_wide_unit2.lldb" > "$RUN_DIR/custody_74mm_wide_unit2.log" 2>&1
