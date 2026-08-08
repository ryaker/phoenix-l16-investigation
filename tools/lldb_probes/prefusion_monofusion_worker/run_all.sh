#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
for pair in \
  "unit1_28mm|/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  "unit1_35mm|/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri" \
  "unit2_28mm|/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"; do
  name=${pair%%|*}
  input=${pair#*|}
  dd if="$input" of=/dev/null bs=4096 count=1 2>/dev/null
  sleep 2
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/$name.lldb"
done
python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_worker/validate_reports.py"
