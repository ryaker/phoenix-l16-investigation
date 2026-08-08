#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
mkdir -p "$ROOT/runs/prefusion_monofusion_color_wrapper"

for name in unit1_28mm unit2_28mm; do
  arch -x86_64 lldb -b -s \
    "$ROOT/tools/lldb_probes/prefusion_monofusion_color_wrapper/$name.lldb"
done

python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_color_wrapper/verify_color_wrapper.py"
