#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
APP=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app
LRI=${CF_LRI:-/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri}
OUTPUT=${CF_RENDER_OUTPUT:-/private/tmp/codex_cf_hotpixel.hdr}

arch -x86_64 lldb -b \
  -o "target create $ROOT/tools/lri_process" \
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_f_runtime/hotpixel_lut_probe.py" \
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=$APP/Contents/Frameworks,DYLD_LIBRARY_PATH=$APP/Contents/Frameworks" \
  -o "breakpoint set --name main --one-shot true" \
  -o "process launch -- \"$LRI\" \"$OUTPUT\" --profile 3 --export-fmt 3 --no-auto-lris" \
  -o "script hotpixel_lut_probe.install(lldb.debugger)" \
  -o continue \
  -o quit
