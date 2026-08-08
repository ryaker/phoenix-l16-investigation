#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/denoise_route_census"
OUT="$ROOT/runs/denoise_route_census"
mkdir -p "$OUT"

for suffix in cnr denoise_algo setdenoise; do
  arch -x86_64 lldb -b -s "$PROBE/unit2_35mm_${suffix}.lldb" \
    > "$OUT/unit2_35mm_${suffix}.log"
done
