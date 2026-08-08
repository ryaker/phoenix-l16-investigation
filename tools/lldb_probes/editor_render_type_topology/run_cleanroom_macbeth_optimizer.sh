#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
CERES_SOURCE="$ROOT/runs/editor_render_type_topology/ceres-solver-1.12.0"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
OUT="$ROOT/runs/editor_render_type_topology/cleanroom_optimize_macbeth"
SOURCE="${1:-$ROOT/runs/editor_color_calibration/photo_exact/unit1/camera_00_type_0_macbeth_f32.raw}"
TARGET="$ROOT/runs/editor_render_type_topology/macbeth_optimizer_target_f32.raw"
TARGET_XYZ="$ROOT/runs/editor_render_type_topology/macbeth_optimizer_roundtrip_xyz_f32.raw"

if [[ ! -f "$CERES_SOURCE/include/ceres/solver.h" ]]; then
  git clone --depth 1 --branch 1.12.0 \
    https://github.com/ceres-solver/ceres-solver.git "$CERES_SOURCE"
fi

clang++ -arch x86_64 -std=c++14 -O2 -Wall -Wextra -ffp-contract=off \
  -DCERES_USE_CXX11 \
  -I"$CERES_SOURCE/include" -I"$CERES_SOURCE/config" \
  -I"$CERES_SOURCE/internal/ceres/miniglog" \
  -I/opt/homebrew/Cellar/eigen/5.0.1/include/eigen3 \
  -L"$FRAMEWORKS" -Wl,-rpath,"$FRAMEWORKS" -lceres \
  "$PROBE/cleanroom_optimize_macbeth.cpp" \
  "$CERES_SOURCE/internal/ceres/miniglog/glog/logging.cc" -o "$OUT"

DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  arch -x86_64 "$OUT" "$SOURCE" "$TARGET" "$TARGET_XYZ"
