#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
for name in unit1_28mm unit1_35mm unit1_70mm unit1_150mm unit2_28mm unit2_70mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_monofusion_identity/$name.lldb"
done
