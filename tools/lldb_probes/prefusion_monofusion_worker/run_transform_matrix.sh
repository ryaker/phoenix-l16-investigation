#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/prefusion_monofusion_worker"
mkdir -p "$OUT"
arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/probe_transform_matrix.c" \
  -o "$OUT/probe_transform_matrix"
DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  arch -x86_64 "$OUT/probe_transform_matrix" \
    "$OUT/transform_forward_matrix.bin" "$OUT/transform_inverse_matrix.bin"

python3 \
  "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/validate_transform_matrix.py"
