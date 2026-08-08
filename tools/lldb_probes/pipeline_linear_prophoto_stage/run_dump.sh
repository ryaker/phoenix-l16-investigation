#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/tools/lldb_probes/pipeline_linear_prophoto_stage/dump_pipeline_color_config.c"
OUT="$ROOT/runs/pipeline_linear_prophoto_stage/dump_pipeline_color_config"

mkdir -p "$(dirname "$OUT")"
clang -arch x86_64 -O2 -Wall -Wextra \
    -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
    "$SRC" -o "$OUT"
DYLD_FRAMEWORK_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
DYLD_LIBRARY_PATH="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks" \
    arch -x86_64 "$OUT"
