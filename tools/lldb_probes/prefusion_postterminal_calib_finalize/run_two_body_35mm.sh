#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_postterminal_calib_finalize"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/prefusion_postterminal_calib_finalize/unit1_35mm.lldb" \
  > "$OUT/unit1_35mm.log" 2>&1
arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/prefusion_postterminal_calib_finalize/unit2_35mm.lldb" \
  > "$OUT/unit2_35mm.log" 2>&1

python3 \
  "$ROOT/tools/lldb_probes/prefusion_postterminal_calib_finalize/verify_postterminal.py"
