#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
PATCH_DIR="$ROOT/runs/final_iramp_image_effect/zero_score"
OUT="$PATCH_DIR/libcp.dylib"
RUNNER="$PATCH_DIR/lri_process_zero_score"
ORIGINAL_RPATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks

python3 \
  "$ROOT/tools/lldb_probes/final_iramp_image_effect/make_zero_score_libcp.py" \
  "$OUT"
codesign --force --sign - "$OUT"
codesign --verify --verbose=2 "$OUT"

cp "$ROOT/tools/lri_process" "$RUNNER"
install_name_tool -delete_rpath "$ORIGINAL_RPATH" "$RUNNER"
install_name_tool -add_rpath "$PATCH_DIR" "$RUNNER"
codesign --force --sign - \
  --entitlements \
  "$ROOT/tools/lldb_probes/final_iramp_image_effect/runner_entitlements.plist" \
  "$RUNNER"
codesign --verify --verbose=2 "$RUNNER"
