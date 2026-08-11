#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LABEL INPUT_LRI OUTPUT_HDR" >&2
  exit 2
fi

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
LABEL=$1
INPUT_LRI=$2
OUTPUT_HDR=$3
OUT_DIR="$ROOT/runs/colorfusion_source_planes/$LABEL"
mkdir -p "$OUT_DIR"
export CF_SOURCE_PLANES_OUT="$OUT_DIR"

arch -x86_64 lldb -b \
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks HL_NUM_THREADS=1 CF_SOURCE_PLANES_OUT=$OUT_DIR" \
  -o "target create $ROOT/tools/lri_process" \
  -o "settings set -- target.run-args \"$INPUT_LRI\" \"$OUTPUT_HDR\" --profile 3 --export-fmt 3 --no-auto-lris" \
  -o "breakpoint set --shlib libcp.dylib --address 0x1abc71" \
  -o run \
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_source_planes/probe.py" \
  -o "script probe.capture(lldb.debugger, lldb.frame)" \
  -o "process kill" \
  -o quit \
  >"$OUT_DIR/lldb.log" 2>&1

cat "$OUT_DIR/capture.json"

