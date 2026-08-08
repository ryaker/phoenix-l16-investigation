#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
SOURCE="/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
export L16_PROBE_LABEL="Unit-1 70mm Guidance collapse2 worker"
export L16_STAGED_LRI=/private/tmp/l16_guidance_collapse2_unit1_70mm.lri
export L16_OUTPUT_HDR=/private/tmp/l16_guidance_collapse2_unit1_70mm.hdr
export L16_TMP_REPORT=/private/tmp/l16_guidance_collapse2_unit1_70mm.json
RUN_DIR="$ROOT/runs/index5_guidance_channel_origin"

mkdir -p "$RUN_DIR"
cp "$SOURCE" "$L16_STAGED_LRI"
test "$(shasum -a 256 "$SOURCE" | awk '{print $1}')" = \
  "$(shasum -a 256 "$L16_STAGED_LRI" | awk '{print $1}')"
rm -f "$L16_OUTPUT_HDR" "$L16_TMP_REPORT"
arch -x86_64 lldb -s \
  "$ROOT/tools/lldb_probes/index5_guidance_channel_origin/collapse2_worker_env.lldb"
cp "$L16_TMP_REPORT" "$RUN_DIR/collapse2_worker_unit1_70mm.json"
rm -f "$L16_STAGED_LRI" "$L16_OUTPUT_HDR" "$L16_TMP_REPORT"
