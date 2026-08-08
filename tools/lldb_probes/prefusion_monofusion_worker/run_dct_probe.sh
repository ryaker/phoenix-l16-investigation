#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
RUN="$ROOT/runs/prefusion_monofusion_worker"
mkdir -p "$RUN"

arch -x86_64 clang -arch x86_64 -O2 -Wall -Wextra \
  -Wl,-rpath,/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/probe_dct.c" \
  -o "$RUN/probe_dct"

DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks \
  arch -x86_64 "$RUN/probe_dct" > "$RUN/dct_probe.txt"

python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/validate_dct_probe.py"
