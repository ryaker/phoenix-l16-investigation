#!/bin/sh
set -eu

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PROBE="$ROOT/tools/lldb_probes/ccm_illuminant_selection"
OUT="$ROOT/runs/ccm_illuminant_selection"

mkdir -p "$OUT"
for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$PROBE/${tier}.lldb" >"$OUT/${tier}.log" 2>&1
done
python3 "$PROBE/verify_ccm_illuminant_selection.py"
