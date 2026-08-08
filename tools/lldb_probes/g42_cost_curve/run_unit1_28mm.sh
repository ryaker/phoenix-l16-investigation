#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
exec "$ROOT/tools/lldb_probes/g42_cost_curve/run_lri.sh" \
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  unit1_28mm 1035 780
