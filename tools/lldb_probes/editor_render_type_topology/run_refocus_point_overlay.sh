#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
LRI="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
INTERPOSE="$RUN/capture_refocus_point_overlay_interpose.dylib"
PROCESS="$RUN/lri_process_refocus_point"
REPORT_WIDE="$RUN/editor_refocus_point_overlay_28mm_max9.json"
REPORT_NARROW="$RUN/editor_refocus_point_overlay_28mm_max0p1.json"

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -ffp-contract=off -fno-omit-frame-pointer \
  -Wall -Wextra -dynamiclib \
  "$PROBE/capture_refocus_point_overlay_interpose.c" \
  "$PROBE/capture_refocus_point_overlay_shim.s" \
  -o "$INTERPOSE"
arch -x86_64 clang++ -arch x86_64 -std=c++17 -stdlib=libc++ -O2 \
  -L"$FRAMEWORKS" -lcp -Wl,-rpath,"$FRAMEWORKS" \
  -framework CoreFoundation -framework CoreGraphics -framework ImageIO \
  -framework CoreServices "$ROOT/tools/lri_process.cpp" -o "$PROCESS"

run_case() {
  local report="$1"
  local max_blur="$2"
  local output="$3"
  L16_REFOCUS_POINT_OUT="$report" DYLD_INSERT_LIBRARIES="$INTERPOSE" \
  DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
    "$PROCESS" "$LRI" "$output" \
    --profile 3 --render-type 1 --render-only --sync-render \
    --construct-depth-editor --renderer-mode 1 --prepare-mode0-rerender \
    --maximum-in-focus-blur-pixels "$max_blur" \
    --dof-f-number 2 --dof-focus-center \
    --gui-level-sweep --no-auto-lris
}

run_case "$REPORT_WIDE" 9 /tmp/editor_refocus_point_overlay_max9.hdr
run_case "$REPORT_NARROW" 0.1 /tmp/editor_refocus_point_overlay_max0p1.hdr

cat "$REPORT_WIDE"
cat "$REPORT_NARROW"
