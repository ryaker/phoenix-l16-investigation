#!/bin/sh
set -eu
ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
SOURCE="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
STAGED=/Users/ryaker/L16_02130_nlm_probe.lri
mkdir -p "$ROOT/runs/nlm_weight_formula"
if [ ! -f "$STAGED" ] || [ "$(stat -f %z "$STAGED")" != "$(stat -f %z "$SOURCE")" ]; then
  cp "$SOURCE" "$STAGED"
fi
OUTPUT=/Users/ryaker/nlm_weight_formula_28mm.hdr
trap 'rm -f "$STAGED" "$OUTPUT"' EXIT
arch -x86_64 lldb -s "$ROOT/tools/lldb_probes/nlm_weight_formula/nlm_weight_formula_28mm.lldb" \
  "$ROOT/tools/lri_process" \
  > "$ROOT/runs/nlm_weight_formula/unit1_28mm.log" 2>&1
if [ -f "$OUTPUT" ]; then
  mv "$OUTPUT" "$ROOT/runs/nlm_weight_formula/unit1_28mm.hdr"
fi
