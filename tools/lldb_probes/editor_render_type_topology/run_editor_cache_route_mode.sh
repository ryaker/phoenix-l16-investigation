#!/usr/bin/env bash
set -euo pipefail

MODE="${1:?usage: run_editor_cache_route_mode.sh MODE [MAXIMUM_IN_FOCUS_BLUR_PIXELS] [single|sweep] [F_NUMBER] [DEBUG_VIEW_ID] [quick]}"
BLUR="${2:-}"
SCHEDULE="${3:-sweep}"
F_NUMBER="${4:-}"
DEBUG_VIEW_ID="${5:-}"
QUICK_SELECT="${6:-}"
ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
LRI="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
INTERPOSE="$RUN/capture_editor_cache_route_interpose.dylib"
SUFFIX="mode${MODE}"
EXTRA_ARGS=()
if [[ -n "$BLUR" ]]; then
  SUFFIX="${SUFFIX}_blur${BLUR//./p}"
  EXTRA_ARGS+=(--maximum-in-focus-blur-pixels "$BLUR")
fi
if [[ "$SCHEDULE" != "single" ]]; then
  EXTRA_ARGS+=(--gui-level-sweep)
fi
if [[ -n "$F_NUMBER" ]]; then
  SUFFIX="${SUFFIX}_f${F_NUMBER//./p}"
  EXTRA_ARGS+=(--dof-f-number "$F_NUMBER" --dof-focus-center)
fi
if [[ -n "$DEBUG_VIEW_ID" ]]; then
  SUFFIX="${SUFFIX}_debug${DEBUG_VIEW_ID//0x/}"
  EXTRA_ARGS+=(--debug-view-id "$DEBUG_VIEW_ID")
fi
if [[ "$QUICK_SELECT" == "quick" ]]; then
  SUFFIX="${SUFFIX}_quick"
  EXTRA_ARGS+=(--quick-select-center)
fi
REPORT="$RUN/editor_cache_route_${SUFFIX}.json"
DUMP="$RUN/editor_cache_output_${SUFFIX}_level4"
MASK_DUMP="$RUN/editor_quick_select_mask_${SUFFIX}.raw"
EXTRA_ARGS+=(--dump-output-level 4 "$DUMP")

clang -arch x86_64 -std=c11 -O2 -fno-omit-frame-pointer -Wall -Wextra -dynamiclib \
  "$PROBE/capture_editor_cache_route_interpose.c" -o "$INTERPOSE"
arch -x86_64 clang++ -arch x86_64 -std=c++17 -stdlib=libc++ -O2 \
  -L"$FRAMEWORKS" -lcp -Wl,-rpath,"$FRAMEWORKS" \
  -framework CoreFoundation -framework CoreGraphics -framework ImageIO \
  -framework CoreServices "$ROOT/tools/lri_process.cpp" \
  -o "$RUN/lri_process_modes"

L16_CACHE_ROUTE_OUT="$REPORT" L16_QUICK_SELECT_MASK_OUT="$MASK_DUMP" \
DYLD_INSERT_LIBRARIES="$INTERPOSE" \
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  "$RUN/lri_process_modes" "$LRI" "/tmp/editor_cache_${SUFFIX}.hdr" \
  --profile 3 --render-type 1 --render-only --sync-render \
  --construct-depth-editor --renderer-mode "$MODE" --prepare-mode0-rerender \
  "${EXTRA_ARGS[@]}" \
  --no-auto-lris
cat "$REPORT"
