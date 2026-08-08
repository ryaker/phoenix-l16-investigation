#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/prefusion_monofusion_mode0_tile/unit1_28mm"
SRC="$ROOT/tools/lldb_probes/prefusion_monofusion_mode0_tile/probe_transform_batch.c"
BIN="$OUT/probe_transform_batch"
FRAMEWORKS=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,"$FRAMEWORKS" "$SRC" -o "$BIN"

DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_mode0_tile/verify_full_overlap.py" \
    --installed-transform-oracle "$BIN"
