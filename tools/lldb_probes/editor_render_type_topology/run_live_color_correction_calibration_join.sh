#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN_DIR="$ROOT/runs/editor_color_calibration"
REPLAY="$RUN_DIR/replay_color_correction"
REPORT="$RUN_DIR/live_28mm_calibration_join.json"

clang -O2 -Wall -Wextra "$PROBE_DIR/replay_color_correction.c" -o "$REPLAY"
python3 "$PROBE_DIR/validate_live_color_correction_from_calibration.py" \
  --map-manifest "$RUN_DIR/two_body_hsv_map_manifest.json" \
  --replay "$REPLAY" \
  --input "$ROOT/runs/editor_render_type_topology/stage_images/display_stage_03_340f70.raw" \
  --expected "$ROOT/runs/editor_render_type_topology/stage_images/display_stage_10_347680.raw" \
  --output-dir "$RUN_DIR/live_candidates" \
  --body unit1 \
  --scene-cct 4953.66357421875 \
  --lower-cct 2855.63232421875 \
  --upper-cct 6502.08203125 > "$REPORT"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("alpha=%s word=%s exact_camera_ids=%s" % (d["alpha"],d["alpha_word"],d["exact_camera_ids"])); print("best=%s" % d["results"][:3])' "$REPORT"
shasum -a 256 "$REPORT"
