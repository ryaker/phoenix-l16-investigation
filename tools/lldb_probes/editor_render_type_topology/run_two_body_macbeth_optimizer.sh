#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN_DIR="$ROOT/runs/editor_color_calibration"
MANIFEST="$RUN_DIR/two_body_macbeth_manifest.json"
EXECUTABLE="$RUN_DIR/probe_optimize_hsv_lut"
REPORT="$RUN_DIR/two_body_hsv_map_manifest.json"

mkdir -p "$RUN_DIR"
python3 "$PROBE_DIR/extract_macbeth_calibration.py" \
  --unit1 "/Volumes/Base Photos/New LRI/Unit 1/calibration.lri" \
  --unit2 "/Volumes/Base Photos/New LRI/Unit 2/calibration.lri" \
  --output-dir "$RUN_DIR/macbeth" > "$MANIFEST"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$PROBE_DIR/probe_optimize_hsv_lut_identity.c" -o "$EXECUTABLE"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
python3 "$PROBE_DIR/batch_optimize_macbeth_maps.py" \
  --manifest "$MANIFEST" \
  --executable "$EXECUTABLE" \
  --output-dir "$RUN_DIR/maps" > "$REPORT"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("optimized_records=%d" % d["result_count"])' "$REPORT"
shasum -a 256 "$MANIFEST" "$REPORT"
