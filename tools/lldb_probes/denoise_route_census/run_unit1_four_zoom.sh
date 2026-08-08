#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/denoise_route_census"
OUT="$ROOT/runs/denoise_route_census"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE/unit1_${tier}.lldb" > "$OUT/unit1_${tier}.log"
done
