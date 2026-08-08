#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
CAL="$ROOT/runs/editor_color_calibration"
CERES_SOURCE="$RUN/ceres-solver-1.12.0"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
INTERPOSE="$RUN/capture_ceres_solve_interpose.dylib"
REPORT="$RUN/ceres_solve_capture.json"
SOURCE="$CAL/photo_exact/unit1/camera_00_type_0_macbeth_f32.raw"
MAP="$RUN/ceres_capture_map.raw"

if [[ ! -f "$CERES_SOURCE/include/ceres/solver.h" ]]; then
  git clone --depth 1 --branch 1.12.0 \
    https://github.com/ceres-solver/ceres-solver.git "$CERES_SOURCE"
fi

clang++ -arch x86_64 -std=c++14 -O2 -Wall -Wextra -dynamiclib \
  -I"$CERES_SOURCE/include" -I"$CERES_SOURCE/config" \
  -I"$CERES_SOURCE/internal/ceres/miniglog" \
  -L"$FRAMEWORKS" -Wl,-rpath,"$FRAMEWORKS" -lceres \
  -undefined dynamic_lookup \
  "$PROBE/capture_ceres_solve_interpose.cpp" -o "$INTERPOSE"
clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,"$FRAMEWORKS" "$PROBE/probe_optimize_hsv_lut_identity.c" \
  -o "$CAL/probe_optimize_hsv_lut"

L16_CERES_CAPTURE_OUT="$REPORT" DYLD_INSERT_LIBRARIES="$INTERPOSE" \
DYLD_FORCE_FLAT_NAMESPACE=1 \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$CAL/probe_optimize_hsv_lut" "$SOURCE" "$MAP" >/dev/null
cat "$REPORT"
