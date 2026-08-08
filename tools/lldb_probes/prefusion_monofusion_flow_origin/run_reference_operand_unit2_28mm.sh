#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
exec "$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/run_reference_operand_unit1_28mm.sh" \
  "Unit-2 exact-28mm MonoFusion A1 reference operand" \
  "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri" \
  "unit2_28mm_reference_operand"
