#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/discriminate_color_correction_source.c"
OUT="$ROOT/runs/editor_render_type_topology/discriminate_color_correction_source"
INPUT="$ROOT/runs/editor_render_type_topology/stage_images/display_stage_03_340f70.raw"
EXPECTED="$ROOT/runs/editor_render_type_topology/stage_images/display_stage_10_347680.raw"

clang -arch x86_64 -O2 -Wall -Wextra \
    -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
    "$SRC" -o "$OUT"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
    arch -x86_64 "$OUT" "$INPUT" "$EXPECTED"
