#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "usage: $0 LRI RUN_LABEL THREADS(default|N) [serialize-executor|serial-executor-2d30]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LRI="$1"
LABEL="$2"
THREADS="$3"
SERIALIZE="${4:-}"
RUN="$ROOT/runs/index5_nondeterminism/$LABEL"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
PROCESS="/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process"
G42_SOURCE="$ROOT/tools/lldb_probes/g42_cost_curve/capture_g42_cost_curve_interpose.c"
BANK_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/capture_create_stereo_banks_interpose.c"
GEOMETRY_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/capture_geometry_banks_interpose.c"
G42_DYLIB="$RUN/capture_g42.dylib"
BANK_DYLIB="$RUN/capture_create_stereo_banks.dylib"
GEOMETRY_DYLIB="$RUN/capture_geometry_banks.dylib"
EXECUTOR_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/serialize_executor_6090_interpose.c"
EXECUTOR_DYLIB="$RUN/serialize_executor_6090.dylib"
WRITE_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/capture_current_bank_writes_interpose.c"
WRITE_DYLIB="$RUN/capture_current_bank_writes.dylib"
SERIAL_2D30_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/force_executor_2d30_serial_interpose.c"
SERIAL_2D30_DYLIB="$RUN/force_executor_2d30_serial.dylib"

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$G42_SOURCE" -o "$G42_DYLIB"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$BANK_SOURCE" -o "$BANK_DYLIB"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$GEOMETRY_SOURCE" -o "$GEOMETRY_DYLIB"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$WRITE_SOURCE" -o "$WRITE_DYLIB"
INSERT="$G42_DYLIB:$BANK_DYLIB:$GEOMETRY_DYLIB:$WRITE_DYLIB"
if [[ "$SERIALIZE" == "serialize-executor" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$EXECUTOR_SOURCE" -o "$EXECUTOR_DYLIB"
  INSERT="$INSERT:$EXECUTOR_DYLIB"
elif [[ "$SERIALIZE" == "serial-executor-2d30" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$SERIAL_2D30_SOURCE" -o "$SERIAL_2D30_DYLIB"
  INSERT="$INSERT:$SERIAL_2D30_DYLIB"
fi

COMMON=(
  L16_G42_CURVE_DIR="$RUN"
  L16_G42_TARGET_X=1035
  L16_G42_TARGET_Y=780
  L16_G42_EXIT_AFTER_CAPTURE=1
  L16_CREATE_STEREO_BANK_REPORT="$RUN/create_stereo_banks.bin"
  L16_GEOMETRY_BANK_REPORT="$RUN/geometry_banks.bin"
  L16_CURRENT_BANK_WRITE_REPORT="$RUN/current_bank_writes.bin"
  L16_EXECUTOR_SERIAL_REPORT="$RUN/executor_serial.txt"
  DYLD_INSERT_LIBRARIES="$INSERT"
  DYLD_FRAMEWORK_PATH="$FRAMEWORKS"
  DYLD_LIBRARY_PATH="$FRAMEWORKS"
)

if [[ "$THREADS" == "default" ]]; then
  env -u HL_NUM_THREADS "${COMMON[@]}" \
    "$PROCESS" "$LRI" "/tmp/${LABEL}.hdr" \
    --profile 3 --export-fmt 3 --no-auto-lris
else
  env HL_NUM_THREADS="$THREADS" "${COMMON[@]}" \
    "$PROCESS" "$LRI" "/tmp/${LABEL}.hdr" \
    --profile 3 --export-fmt 3 --no-auto-lris
fi

test -s "$RUN/report.json"
test -s "$RUN/create_stereo_banks.bin"
test -s "$RUN/geometry_banks.bin"
test -s "$RUN/current_bank_writes.bin"
