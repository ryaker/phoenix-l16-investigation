#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
LRI="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
INTERPOSE="$RUN/capture_editor_dof_math_interpose.dylib"
REPORT="$RUN/editor_dof_math_mode1_blur9_f2.json"

clang -arch x86_64 -std=c11 -O2 -Wall -Wextra -dynamiclib \
  "$PROBE/capture_editor_dof_math_interpose.c" -o "$INTERPOSE"
arch -x86_64 clang++ -arch x86_64 -std=c++17 -stdlib=libc++ -O2 \
  -L"$FRAMEWORKS" -lcp -Wl,-rpath,"$FRAMEWORKS" \
  -framework CoreFoundation -framework CoreGraphics -framework ImageIO \
  -framework CoreServices "$ROOT/tools/lri_process.cpp" \
  -o "$RUN/lri_process_dof_math"

L16_DOF_MATH_OUT="$REPORT" DYLD_INSERT_LIBRARIES="$INTERPOSE" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$RUN/lri_process_dof_math" "$LRI" "/tmp/editor_dof_math.hdr" \
  --profile 3 --render-type 1 --render-only --sync-render --gui-level-sweep \
  --construct-depth-editor --renderer-mode 1 --prepare-mode0-rerender \
  --maximum-in-focus-blur-pixels 9 --dof-f-number 2 --dof-focus-center \
  --no-auto-lris
cat "$REPORT"
