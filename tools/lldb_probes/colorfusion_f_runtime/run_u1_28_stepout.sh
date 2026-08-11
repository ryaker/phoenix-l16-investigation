#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p "$ROOT/runs/colorfusion_f_runtime/u1_28"

# Keeping the breakpoint disabled during each synchronous step-out prevents
# another worker from stealing LLDB's stop while the selected worker returns.
LLDB_ARGS=(
  -b
  -o "settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks HL_NUM_THREADS=1"
  -o "target create $ROOT/tools/lri_process"
  -o "settings set -- target.run-args \"/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri\" /tmp/cf_runtime_u1_28.hdr --profile 3 --export-fmt 3 --no-auto-lris"
  -o "breakpoint set --shlib libcp.dylib --address 0x18eb00"
  -o run
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_f_runtime/probe.py"
  -o "script probe.manual_pre(lldb.frame)"
  -o "breakpoint disable 1"
  -o "thread step-out"
  -o "script probe.manual_post(lldb.frame)"
  -o "breakpoint enable 1"
  -o continue
  -o "script probe.manual_pre(lldb.frame)"
  -o "breakpoint disable 1"
  -o "thread step-out"
  -o "script probe.manual_post(lldb.frame)"
  -o "breakpoint enable 1"
  -o continue
  -o "script probe.manual_pre(lldb.frame)"
  -o "breakpoint disable 1"
  -o "thread step-out"
  -o "script probe.manual_post(lldb.frame)"
  -o "script probe.arm_numerator(lldb.frame)"
  -o continue
  -o "script probe.manual_numerator(lldb.frame)"
  -o continue
  -o "script probe.manual_output(lldb.frame)"
  -o "process kill"
  -o quit
)

arch -x86_64 lldb "${LLDB_ARGS[@]}"
