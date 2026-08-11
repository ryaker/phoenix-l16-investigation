#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
APP=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app

arch -x86_64 lldb -b \
  -o "target create $ROOT/tools/lri_process" \
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_f_runtime/noise_signal_origin_probe.py" \
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=$APP/Contents/Frameworks,DYLD_LIBRARY_PATH=$APP/Contents/Frameworks" \
  -o "breakpoint set --name main --one-shot true" \
  -o "process launch -- /Volumes/Base\ Photos/Light/2018-07-23/L16_02130.lri /private/tmp/codex_cf_noise_origin.hdr --profile 3 --export-fmt 3 --no-auto-lris" \
  -o "script noise_signal_origin_probe.install(lldb.debugger)" \
  -o continue \
  -o "script noise_signal_origin_probe.capture(lldb.debugger)" \
  -o quit
