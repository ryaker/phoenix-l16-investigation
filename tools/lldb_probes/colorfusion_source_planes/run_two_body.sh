#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
"$ROOT/tools/lldb_probes/colorfusion_source_planes/run_one.sh" \
  u1_28 \
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  "$ROOT/runs/colorfusion_source_planes/u1_28.hdr"
"$ROOT/tools/lldb_probes/colorfusion_source_planes/run_one.sh" \
  u2_70 \
  "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri" \
  "$ROOT/runs/colorfusion_source_planes/u2_70.hdr"
