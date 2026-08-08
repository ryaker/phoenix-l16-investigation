#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/probe_optimize_hsv_lut_identity.c"
OUT="$ROOT/runs/editor_render_type_topology/probe_optimize_hsv_lut_identity"
MAP="$ROOT/runs/editor_render_type_topology/identity_hsv_map_vec4_f32.raw"
REPORT="$ROOT/runs/editor_render_type_topology/identity_hsv_map.json"
REFERENCE="$ROOT/runs/editor_render_type_topology/macbeth_optimizer_target_f32.raw"

mkdir -p "$(dirname "$OUT")"
"$ROOT/tools/lldb_probes/editor_render_type_topology/run_macbeth_reference_dump.sh" >/dev/null
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$SRC" -o "$OUT"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
arch -x86_64 "$OUT" "$REFERENCE" "$MAP" > "$REPORT"
cat "$REPORT"
shasum -a 256 "$MAP"
