#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 4 ]]; then
  echo "usage: $0 LRI RUN_LABEL [TARGET_X TARGET_Y]" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/g42_cost_curve"
LRI="$1"
LABEL="$2"
TARGET_X="${3:-1035}"
TARGET_Y="${4:-780}"
RUN="$ROOT/runs/g42_cost_curve/$LABEL"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
INTERPOSE="$RUN/capture_g42_cost_curve_interpose.dylib"

if [[ ! -f "$LRI" ]]; then
  echo "missing LRI: $LRI" >&2
  exit 2
fi

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -fno-omit-frame-pointer -Wall -Wextra \
  -dynamiclib "$PROBE/capture_g42_cost_curve_interpose.c" -o "$INTERPOSE"

L16_G42_CURVE_DIR="$RUN" \
L16_G42_TARGET_X="$TARGET_X" \
L16_G42_TARGET_Y="$TARGET_Y" \
DYLD_INSERT_LIBRARIES="$INTERPOSE" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" \
DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$ROOT/tools/lri_process" "$LRI" "/tmp/g42_cost_curve_${LABEL}.hdr" \
  --profile 3 --export-fmt 3 --no-auto-lris

cat "$RUN/status.txt"
if [[ -s "$RUN/report.json" ]]; then
  cat "$RUN/report.json"
fi
