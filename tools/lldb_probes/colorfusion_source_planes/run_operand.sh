#!/usr/bin/env bash
set -euo pipefail
ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
LABEL=${1:-u1_28}
INPUT_LRI=${2:-/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri}
OUT_DIR="$ROOT/runs/colorfusion_source_planes/${LABEL}_operands"
mkdir -p "$OUT_DIR"
FW=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
arch -x86_64 lldb -b \
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=$FW DYLD_LIBRARY_PATH=$FW HL_NUM_THREADS=1" \
  -o "target create $ROOT/tools/lri_process" \
  -o "settings set -- target.run-args \"$INPUT_LRI\" \"$OUT_DIR/out.hdr\" --profile 3 --export-fmt 3 --no-auto-lris" \
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_source_planes/operand_probe.py" \
  -o "script operand_probe.reset('$OUT_DIR/operands.json')" \
  -o "breakpoint set --shlib libcp.dylib --address 0x1ab813" \
  -o "breakpoint command add -s python -o 'return operand_probe.hitrect(frame,bp_loc,internal_dict)'" \
  -o "breakpoint set --shlib libcp.dylib --address 0x1aba80" \
  -o "breakpoint command add -s python -o 'return operand_probe.hit390(frame,bp_loc,internal_dict)'" \
  -o "breakpoint set --shlib libcp.dylib --address 0x1aba8f" \
  -o "breakpoint command add -s python -o 'return operand_probe.hitbd20(frame,bp_loc,internal_dict)'" \
  -o "breakpoint set --shlib libcp.dylib --address 0x1abc71" \
  -o run \
  -o "script operand_probe.write()" \
  -o "process kill" \
  -o quit \
  >"$OUT_DIR/lldb.log" 2>&1
echo "=== operands.json ==="
cat "$OUT_DIR/operands.json"
