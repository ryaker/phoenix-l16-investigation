#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/ccm_chromaticity_origin"
FRAMEWORKS=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
mkdir -p "$OUT"

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,"$FRAMEWORKS" \
  "$ROOT/tools/lldb_probes/ccm_chromaticity_origin/dump_ccm_chromaticity.c" \
  -o "$OUT/dump_ccm_chromaticity"

DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  arch -x86_64 "$OUT/dump_ccm_chromaticity" | tee "$OUT/dump.txt"

python3 "$ROOT/tools/lldb_probes/ccm_chromaticity_origin/verify_ccm_chromaticity_origin.py"
