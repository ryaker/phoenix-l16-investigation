#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/prefusion_monofusion_mode0_tile/unit1_28mm"
SRC="$ROOT/tools/lldb_probes/prefusion_monofusion_mode0_tile/probe_inverse_coarse.c"
BIN="$OUT/probe_inverse_stages"
INPUT="$OUT/patch_source_coeff_post.f32le"
FRAMEWORKS=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks

arch -x86_64 clang -O0 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,"$FRAMEWORKS" "$SRC" -o "$BIN"

for stage in coarse stride2 stride1row; do
  DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
    arch -x86_64 "$BIN" "$INPUT" "$OUT/inverse_${stage}.f32le" "$stage"
done

python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_mode0_tile/verify_mode0_tile.py"
