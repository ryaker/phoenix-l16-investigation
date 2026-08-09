#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 5 ]]; then
  echo "usage: $0 LRI RUN_LABEL [SEED [TARGET_X TARGET_Y]]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LRI="$1"
LABEL="$2"
SEED="${3:-305419896}"
TARGET_X="${4:-1035}"
TARGET_Y="${5:-780}"
RUN="$ROOT/runs/index5_nondeterminism_random_device/$LABEL"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
PROCESS="/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process"
G42_SRC="$ROOT/tools/lldb_probes/g42_cost_curve/capture_g42_cost_curve_interpose.c"
RNG_SRC="$ROOT/tools/lldb_probes/index5_nondeterminism_random_device/random_device_control.c"
G42_DYLIB="$RUN/capture_g42.dylib"
RNG_DYLIB="$RUN/control_random_device.dylib"

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$G42_SRC" -o "$G42_DYLIB"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$RNG_SRC" -o "$RNG_DYLIB"

L16_G42_CURVE_DIR="$RUN" \
L16_G42_TARGET_X="$TARGET_X" \
L16_G42_TARGET_Y="$TARGET_Y" \
L16_G42_EXIT_AFTER_CAPTURE=1 \
L16_RANDOM_DEVICE_SEED="$SEED" \
L16_RANDOM_DEVICE_REPORT="$RUN/random_device_report.json" \
DYLD_INSERT_LIBRARIES="$G42_DYLIB:$RNG_DYLIB" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" \
DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$PROCESS" "$LRI" "/tmp/${LABEL}.hdr" \
  --profile 3 --export-fmt 3 --no-auto-lris

test -s "$RUN/report.json"
