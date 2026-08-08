#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
LRI="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
INTERPOSE="$RUN/capture_refocus_slider_formula_interpose.dylib"
PROCESS="$RUN/lri_process_refocus_slider"
REPORT="$RUN/editor_refocus_slider_formula_28mm.json"

mkdir -p "$RUN"
clang -arch x86_64 -std=c11 -O2 -ffp-contract=off -fno-omit-frame-pointer \
  -Wall -Wextra -dynamiclib "$PROBE/capture_refocus_slider_formula_interpose.c" \
  -o "$INTERPOSE"
arch -x86_64 clang++ -arch x86_64 -std=c++17 -stdlib=libc++ -O2 \
  -L"$FRAMEWORKS" -lcp -Wl,-rpath,"$FRAMEWORKS" \
  -framework CoreFoundation -framework CoreGraphics -framework ImageIO \
  -framework CoreServices "$ROOT/tools/lri_process.cpp" -o "$PROCESS"

L16_REFOCUS_SLIDER_OUT="$REPORT" DYLD_INSERT_LIBRARIES="$INTERPOSE" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$PROCESS" "$LRI" /tmp/editor_refocus_slider_formula.hdr \
  --profile 3 --render-type 1 --render-only --sync-render \
  --construct-depth-editor --renderer-mode 2 --prepare-mode0-rerender \
  --maximum-in-focus-blur-pixels 9 --dof-f-number 2 --dof-focus-center \
  --gui-level-sweep --no-auto-lris

cat "$REPORT"
