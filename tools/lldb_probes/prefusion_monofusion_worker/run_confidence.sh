#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
for name in confidence_unit1_35mm confidence_unit2_28mm; do
  arch -x86_64 lldb -b -s \
    "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/$name.lldb"
done
