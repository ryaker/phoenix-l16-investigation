#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p "$ROOT/runs/colorfusion_f_runtime/u1_28"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/colorfusion_f_runtime/run_u1_28.lldb" \
  "$ROOT/tools/lri_process"
