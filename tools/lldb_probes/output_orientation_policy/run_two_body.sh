#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/output_orientation_policy"
RUNS="$ROOT/runs/output_orientation_policy"

mkdir -p "$RUNS"
for sample in unit2_35mm_cw unit1_35mm_ccw; do
  arch -x86_64 lldb -b -s "$PROBE/$sample.lldb" >"$RUNS/$sample.log" 2>&1
  rm -f "$RUNS/$sample.hdr"
done
