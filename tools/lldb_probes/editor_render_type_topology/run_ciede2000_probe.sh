#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/editor_render_type_topology"
RUN="$ROOT/runs/editor_render_type_topology"
FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"

clang -arch x86_64 -std=c11 -O2 -Wall -Wextra \
  -Wl,-rpath,"$FRAMEWORKS" "$PROBE/probe_ciede2000.c" \
  -o "$RUN/probe_ciede2000"
DYLD_FRAMEWORK_PATH="$FRAMEWORKS" DYLD_LIBRARY_PATH="$FRAMEWORKS" \
  arch -x86_64 "$RUN/probe_ciede2000" \
  > "$RUN/ciede2000_probe.json"
cat "$RUN/ciede2000_probe.json"
