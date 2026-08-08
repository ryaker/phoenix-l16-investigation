#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/denoise_route_census"
OUT="$ROOT/runs/denoise_route_census"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$PROBE/unit1_35mm_denoise_selector.lldb" \
  > "$OUT/unit1_35mm_denoise_selector.log" 2>&1

arch -x86_64 lldb -b -s "$PROBE/unit2_35mm_denoise_selector.lldb" \
  > "$OUT/unit2_35mm_denoise_selector.log" 2>&1
