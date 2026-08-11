#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
PHOENIX=/Users/ryaker/L16_Phoenix/phoenix
FRAMEWORKS=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
OUT="$ROOT/runs/colorfusion_f_runtime"

mkdir -p "$OUT" "$ROOT/runs/ccm_chromaticity_origin"

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,"$FRAMEWORKS" \
  "$ROOT/tools/lldb_probes/ccm_chromaticity_origin/dump_ccm_chromaticity.c" \
  -o "$ROOT/runs/ccm_chromaticity_origin/dump_ccm_chromaticity"

c++ -std=c++20 -O2 -ffp-contract=off -I"$PHOENIX/engine" \
  "$ROOT/tools/verifiers/verify_colorfusion_highlight_join.cpp" \
  "$PHOENIX/engine/depth/highlight_restore.cpp" \
  -o "$OUT/verify_colorfusion_highlight_join"

python3 "$ROOT/tools/verifiers/verify_colorfusion_noise_public_origin.py" --case u1_28
python3 "$ROOT/tools/verifiers/verify_colorfusion_noise_public_origin.py" --case u2_70

"$OUT/verify_colorfusion_highlight_join" \
  "$OUT/u1_28_highlight_join/post_hotpixel_u16.bin" \
  "$OUT/u1_28_highlight_join/post_highlight_u16.bin" \
  1 0 0.5821268558502197 0.6293906569480896 parity

"$OUT/verify_colorfusion_highlight_join" \
  "$OUT/u2_70_highlight_join/post_hotpixel_u16.bin" \
  "$OUT/u2_70_highlight_join/post_highlight_u16.bin" \
  1 1 0.6094192862510681 0.514792799949646 parity
