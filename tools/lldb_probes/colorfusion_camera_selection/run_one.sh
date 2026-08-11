#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LABEL INPUT_LRI OUTPUT_IMAGE" >&2
  exit 2
fi

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
LABEL=$1
INPUT_LRI=$2
OUTPUT_IMAGE=$3
OUT_DIR="$ROOT/runs/colorfusion_camera_selection"
mkdir -p "$OUT_DIR"
export CF_SELECTION_OUT="$OUT_DIR/${LABEL}.json"

LLDB_ARGS=(
  -b
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks HL_NUM_THREADS=1"
  -o "target create $ROOT/tools/lri_process"
  -o "settings set -- target.run-args \"$INPUT_LRI\" \"$OUTPUT_IMAGE\" --profile 3 --export-fmt 3 --no-auto-lris"
  -o "breakpoint set --shlib libcp.dylib --address 0x18eb00"
  -o run
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_camera_selection/probe.py"
  -o "script probe.capture(lldb.frame)"
  -o "process kill"
  -o quit
)

arch -x86_64 lldb "${LLDB_ARGS[@]}" \
  >"$OUT_DIR/${LABEL}.lldb.log" 2>&1
cat "$OUT_DIR/${LABEL}.json"
