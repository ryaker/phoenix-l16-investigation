#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/reference_undistorted_planes/unit1_28mm_entry_smoke"
mkdir -p "$OUT"
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/reference_undistorted_planes/unit1_28mm_entry_smoke.lldb" \
  "$ROOT/tools/lri_process" >"$OUT/session.log" 2>&1
rg -q "rdi = 0x" "$OUT/session.log"
echo "undistort_entry_smoke=OK"
