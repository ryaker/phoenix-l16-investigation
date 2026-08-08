#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
SRC="$1"; LABEL="$2"
OUT="$ROOT/runs/normalization_black_level/$LABEL"
mkdir -p "$OUT"
FW=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
arch -x86_64 lldb -b \
  -o "command script import $ROOT/tools/lldb_probes/normalization_black_level/black_probe6.py" \
  -o "script black_probe6.reset('$OUT/solve.json')" \
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=$FW DYLD_LIBRARY_PATH=$FW" \
  -o "target create $ROOT/tools/lri_process" \
  -o "breakpoint set --shlib libcp.dylib --address 0xf36f0" \
  -o "breakpoint set --shlib libcp.dylib --address 0xf3888" \
  -o "script black_probe6.attach(lldb.debugger)" \
  -o "process launch -- \"$SRC\" \"$OUT/out6.hdr\" --export-fmt 3 --no-lris" \
  -o "quit" > "$OUT/run6.log" 2>&1
echo "rc=$? label=$LABEL"
