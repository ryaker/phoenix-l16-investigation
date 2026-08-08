#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
SOURCE="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
STAGED=/private/tmp/l16_guidance_softisp_unit1_28mm.lri
REPORT=/private/tmp/l16_guidance_softisp_unit1_28mm.json
RUN_DIR="$ROOT/runs/index5_guidance_channel_origin"

mkdir -p "$RUN_DIR"
cp "$SOURCE" "$STAGED"
test "$(shasum -a 256 "$SOURCE" | awk '{print $1}')" = \
  "$(shasum -a 256 "$STAGED" | awk '{print $1}')"
rm -f "$REPORT" /private/tmp/l16_guidance_softisp_unit1_28mm.hdr
arch -x86_64 lldb -s \
  "$ROOT/tools/lldb_probes/index5_guidance_channel_origin/softisp_properties_unit1_28mm.lldb"
cp "$REPORT" "$RUN_DIR/softisp_properties_unit1_28mm.json"
rm -f "$STAGED" "$REPORT" /private/tmp/l16_guidance_softisp_unit1_28mm.hdr
