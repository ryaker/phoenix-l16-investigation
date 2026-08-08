#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/iramp_score_kernel"
mkdir -p "$OUT"

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$ROOT/tools/lldb_probes/iramp_score_kernel/replay_36cde0.c" \
  -o "$OUT/replay_36cde0"

if [ -f "$OUT/unit1_35mm/scratch.bin" ]; then
  DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
    arch -x86_64 "$OUT/replay_36cde0" \
      "$OUT/unit1_35mm/scratch.bin" \
      "$OUT/unit1_35mm/candidate.bin"
fi

python3 "$ROOT/tools/lldb_probes/iramp_score_kernel/verify_iramp_score_kernel.py"
