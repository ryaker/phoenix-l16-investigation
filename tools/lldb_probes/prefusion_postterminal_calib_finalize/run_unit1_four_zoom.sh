#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_postterminal_calib_finalize"
OUT="$ROOT/runs/prefusion_postterminal_calib_finalize"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE/unit1_${tier}.lldb" > "$OUT/unit1_${tier}.log"
done
