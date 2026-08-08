#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
CAL="$ROOT/runs/editor_color_calibration"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
UNIT1="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
UNIT2="/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"

mkdir -p "$RUN" "$CAL/photo_exact" "$CAL/photo_exact_maps"

clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$PROBE/capture_color_correction_map_interpose.c" \
  -o "$RUN/capture_color_correction_map_interpose.dylib"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,"$FRAMEWORKS" \
  "$PROBE/probe_chromaticity_cct.c" -o "$RUN/probe_chromaticity_cct"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,"$FRAMEWORKS" \
  "$PROBE/probe_optimize_hsv_lut_identity.c" \
  -o "$CAL/probe_optimize_hsv_lut"
clang -O2 -Wall -Wextra -ffp-contract=off \
  "$PROBE/replay_color_correction.c" -o "$RUN/replay_color_correction"
"$PROBE/run_macbeth_reference_dump.sh" > "$RUN/macbeth_reference_dump.log"

python3 "$PROBE/extract_macbeth_calibration.py" \
  --unit1 "$UNIT1" --unit2 "$UNIT2" \
  --output-dir "$CAL/photo_exact" > "$CAL/photo_exact_macbeth_manifest.json"
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  python3 "$PROBE/batch_optimize_macbeth_maps.py" \
  --manifest "$CAL/photo_exact_macbeth_manifest.json" \
  --executable "$CAL/probe_optimize_hsv_lut" \
  --output-dir "$CAL/photo_exact_maps" \
  > "$CAL/photo_exact_hsv_map_manifest.json"

"$PROBE/run_cleanroom_macbeth_optimizer.sh" \
  > "$RUN/cleanroom_macbeth_optimizer.json"
"$PROBE/run_ceres_solve_capture.sh" \
  > "$RUN/ceres_solve_capture.log"
"$PROBE/run_ciede2000_probe.sh" \
  > "$RUN/ciede2000_probe.log"

L16_COLOR_MAP_OUT="$RUN/color_correction_hsv_map_vec4_f32.raw" \
L16_COLOR_MAP_META="$RUN/color_correction_hsv_map_capture.json" \
L16_COLOR_OWNER_OUT="$RUN/color_correction_owner_0x200.raw" \
L16_COLOR_CONVERT_OUT="$RUN/color_correction_after_convert_f32.raw" \
L16_COLOR_CONVERT_META="$RUN/color_correction_convert_capture.json" \
L16_COLOR_INPUT_CONFIG_OUT="$RUN/color_correction_input_config.raw" \
L16_COLOR_OUTPUT_CONFIG_OUT="$RUN/color_correction_output_config.raw" \
DYLD_INSERT_LIBRARIES="$RUN/capture_color_correction_map_interpose.dylib" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$RUN/lri_process_probe" "$UNIT1" /tmp/color_correction_unused.hdr \
  --profile 3 --render-type 1 --render-only --sync-render \
  --gui-level-sweep --no-auto-lris

read -r X Y < <(python3 -c \
  'import struct,sys; b=open(sys.argv[1],"rb").read(); print(*struct.unpack_from("<2f",b,12))' \
  "$RUN/color_correction_owner_0x200.raw")
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  arch -x86_64 "$RUN/probe_chromaticity_cct" "$X" "$Y" \
  > "$RUN/color_correction_cct.json"

python3 "$PROBE/verify_color_correction_optimizer_static.py" \
  > "$RUN/color_correction_optimizer_static.json"
python3 "$PROBE/verify_live_color_correction_public_join.py" \
  > "$RUN/live_color_correction_public_join_verification.json"
cat "$RUN/live_color_correction_public_join_verification.json"
shasum -a 256 \
  "$CAL/photo_exact_macbeth_manifest.json" \
  "$CAL/photo_exact_hsv_map_manifest.json" \
  "$RUN/live_color_correction_public_join_verification.json"
