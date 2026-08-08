#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/reference_undistorted_planes/unit1_28mm_cache_exit_smoke"
mkdir -p "$OUT"
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/reference_undistorted_planes/unit1_28mm_cache_exit_smoke.lldb" \
  "$ROOT/tools/lri_process" >"$OUT/session.log" 2>&1
rg -q "r14 = 0x" "$OUT/session.log"
echo "source_cache_exit_smoke=OK"
