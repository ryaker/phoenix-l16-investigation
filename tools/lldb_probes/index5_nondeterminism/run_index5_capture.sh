#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "usage: $0 LRI RUN_LABEL THREADS(default|N) [measure-overlap|serialize-mode8|serialize-executor|serial-executor-2d30|freeze-calibration|serialize-mode8+freeze-calibration]" >&2
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
SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/capture_index5_interpose.c"
DYLIB="$RUN/capture_index5.dylib"
SERIAL_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/serialize_mode8_worker_interpose.c"
SERIAL_DYLIB="$RUN/serialize_mode8_worker.dylib"
EXECUTOR_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/serialize_executor_6090_interpose.c"
EXECUTOR_DYLIB="$RUN/serialize_executor_6090.dylib"
FREEZE_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/suppress_dynamic_calibration_interpose.c"
FREEZE_DYLIB="$RUN/suppress_dynamic_calibration.dylib"
SERIAL_2D30_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/force_executor_2d30_serial_interpose.c"
SERIAL_2D30_DYLIB="$RUN/force_executor_2d30_serial.dylib"
OVERLAP_SOURCE="$ROOT/tools/lldb_probes/index5_nondeterminism/measure_mode8_overlap_interpose.c"
OVERLAP_DYLIB="$RUN/measure_mode8_overlap.dylib"

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$SOURCE" -o "$DYLIB"
INSERT="$DYLIB"
if [[ "$SERIALIZE" == "serialize-mode8" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$SERIAL_SOURCE" -o "$SERIAL_DYLIB"
  INSERT="$DYLIB:$SERIAL_DYLIB"
elif [[ "$SERIALIZE" == "measure-overlap" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$OVERLAP_SOURCE" -o "$OVERLAP_DYLIB"
  INSERT="$DYLIB:$OVERLAP_DYLIB"
elif [[ "$SERIALIZE" == "serialize-executor" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$EXECUTOR_SOURCE" -o "$EXECUTOR_DYLIB"
  INSERT="$DYLIB:$EXECUTOR_DYLIB"
elif [[ "$SERIALIZE" == "freeze-calibration" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$FREEZE_SOURCE" -o "$FREEZE_DYLIB"
  INSERT="$DYLIB:$FREEZE_DYLIB"
elif [[ "$SERIALIZE" == "serial-executor-2d30" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$SERIAL_2D30_SOURCE" -o "$SERIAL_2D30_DYLIB"
  INSERT="$DYLIB:$SERIAL_2D30_DYLIB"
elif [[ "$SERIALIZE" == "serialize-mode8+freeze-calibration" ]]; then
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$SERIAL_SOURCE" -o "$SERIAL_DYLIB"
  clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
    "$FREEZE_SOURCE" -o "$FREEZE_DYLIB"
  INSERT="$DYLIB:$SERIAL_DYLIB:$FREEZE_DYLIB"
fi

EXTRA_ENV=(
  L16_CALIBRATION_SUPPRESSION_REPORT="$RUN/calibration_suppression.txt"
  L16_EXECUTOR_SERIAL_REPORT="$RUN/executor_serial.txt"
  L16_MODE8_OVERLAP_REPORT="$RUN/mode8_overlap.txt"
)

if [[ "$THREADS" == "default" ]]; then
  env -u HL_NUM_THREADS \
    "${EXTRA_ENV[@]}" \
    L16_INDEX5_CAPTURE_DIR="$RUN" \
    L16_INDEX5_EXIT_AFTER_CAPTURE=1 \
    DYLD_INSERT_LIBRARIES="$INSERT" \
    DYLD_FRAMEWORK_PATH="$FRAMEWORKS" \
    DYLD_LIBRARY_PATH="$FRAMEWORKS" \
    "$PROCESS" "$LRI" "/tmp/${LABEL}.hdr" \
    --profile 3 --export-fmt 3 --no-auto-lris
else
  env HL_NUM_THREADS="$THREADS" \
    "${EXTRA_ENV[@]}" \
    L16_INDEX5_CAPTURE_DIR="$RUN" \
    L16_INDEX5_EXIT_AFTER_CAPTURE=1 \
    DYLD_INSERT_LIBRARIES="$INSERT" \
    DYLD_FRAMEWORK_PATH="$FRAMEWORKS" \
    DYLD_LIBRARY_PATH="$FRAMEWORKS" \
    "$PROCESS" "$LRI" "/tmp/${LABEL}.hdr" \
    --profile 3 --export-fmt 3 --no-auto-lris
fi

test -s "$RUN/report.json"
test "$(wc -c < "$RUN/index5_hypothesis_index.u16le")" -eq 6489600
