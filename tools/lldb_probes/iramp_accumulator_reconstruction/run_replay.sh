#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT="$ROOT/runs/iramp_accumulator_reconstruction"
INPUT="$OUT/unit1_35mm"
mkdir -p "$OUT"

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$ROOT/tools/lldb_probes/iramp_accumulator_reconstruction/replay_36e530.c" \
  -o "$OUT/replay_36e530"

arch -x86_64 clang -O2 -Wall -Wextra -arch x86_64 \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$ROOT/tools/lldb_probes/iramp_accumulator_reconstruction/dump_transform_basis.c" \
  -o "$OUT/dump_transform_basis"

DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  arch -x86_64 "$OUT/replay_36e530" \
    "$INPUT/before.bin" \
    "$INPUT/after.bin"

DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  arch -x86_64 "$OUT/replay_36e530" \
    "$OUT/unit1_35mm_nonbaseline/before.bin" \
    "$OUT/unit1_35mm_nonbaseline/after.bin"

DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  arch -x86_64 "$OUT/dump_transform_basis" "$OUT/transform_basis.bin"

python3 \
  "$ROOT/tools/lldb_probes/iramp_accumulator_reconstruction/analyze_transform_basis.py" \
  "$OUT/transform_basis.bin"

python3 \
  "$ROOT/tools/lldb_probes/iramp_accumulator_reconstruction/verify_accumulator_reconstruction.py"

python3 \
  "$ROOT/tools/lldb_probes/iramp_baseline_seed/verify_iramp_baseline_seed.py"
