#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/dump_macbeth_reference_table.c"
OUT="$ROOT/runs/editor_render_type_topology/dump_macbeth_reference_table"
REPORT="$ROOT/runs/editor_render_type_topology/macbeth_reference_table.json"
RAW="$ROOT/runs/editor_render_type_topology/macbeth_reference_table_f32.raw"
TARGET="$ROOT/runs/editor_render_type_topology/macbeth_optimizer_target_f32.raw"
ROUNDTRIP="$ROOT/runs/editor_render_type_topology/macbeth_optimizer_roundtrip_xyz_f32.raw"

mkdir -p "$(dirname "$OUT")"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$SRC" -o "$OUT"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
arch -x86_64 "$OUT" "$RAW" "$TARGET" "$ROUNDTRIP" > "$REPORT"
cat "$REPORT"
shasum -a 256 "$RAW" "$TARGET" "$ROUNDTRIP"
