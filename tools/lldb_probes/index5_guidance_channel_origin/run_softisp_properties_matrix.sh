#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
RUN_DIR="$ROOT/runs/index5_guidance_channel_origin"
SCRIPT="$ROOT/tools/lldb_probes/index5_guidance_channel_origin/softisp_properties_env.lldb"
mkdir -p "$RUN_DIR"

run_one() {
  local slug="$1"
  local label="$2"
  local source="$3"
  export L16_PROBE_LABEL="$label"
  export L16_STAGED_LRI="/private/tmp/l16_guidance_softisp_${slug}.lri"
  export L16_OUTPUT_HDR="/private/tmp/l16_guidance_softisp_${slug}.hdr"
  export L16_TMP_REPORT="/private/tmp/l16_guidance_softisp_${slug}.json"
  cp "$source" "$L16_STAGED_LRI"
  test "$(shasum -a 256 "$source" | awk '{print $1}')" = \
    "$(shasum -a 256 "$L16_STAGED_LRI" | awk '{print $1}')"
  rm -f "$L16_OUTPUT_HDR" "$L16_TMP_REPORT"
  arch -x86_64 lldb -s "$SCRIPT"
  cp "$L16_TMP_REPORT" "$RUN_DIR/softisp_properties_${slug}.json"
  rm -f "$L16_STAGED_LRI" "$L16_OUTPUT_HDR" "$L16_TMP_REPORT"
}

run_one unit1_28mm "Unit-1 28mm CreateStereoImage live SoftISP properties" \
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
run_one unit1_35mm "Unit-1 35mm CreateStereoImage live SoftISP properties" \
  "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
run_one unit1_70mm "Unit-1 70mm CreateStereoImage live SoftISP properties" \
  "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
run_one unit1_150mm "Unit-1 150mm CreateStereoImage live SoftISP properties" \
  "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
run_one unit2_28mm "Unit-2 28mm CreateStereoImage live SoftISP properties" \
  "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"
