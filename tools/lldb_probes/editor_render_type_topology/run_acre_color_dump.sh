#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/dump_acre_color_conversion.c"
OUT="$ROOT/runs/editor_render_type_topology/dump_acre_color_conversion"

clang -arch x86_64 -O2 -Wall -Wextra \
    -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
    "$SRC" -o "$OUT"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
    arch -x86_64 "$OUT"
