#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/index5_composed_geometry_origin"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/index5_composed_geometry_origin/composed_geometry_${tier}.lldb" > "$OUT/composed_geometry_${tier}.log"
done
