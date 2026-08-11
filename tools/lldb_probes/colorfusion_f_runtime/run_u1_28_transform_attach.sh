#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p "$ROOT/runs/colorfusion_f_runtime/u1_28_transform"

arch -x86_64 lldb -b \
  -o "target create $ROOT/tools/lri_process" \
  -o "command script import $ROOT/tools/lldb_probes/colorfusion_f_runtime/transform_attach_probe.py" \
  -o "process attach --name lri_process" \
  -o "script transform_attach_probe.install(lldb.debugger)" \
  -o continue \
  -o continue \
  -o quit
