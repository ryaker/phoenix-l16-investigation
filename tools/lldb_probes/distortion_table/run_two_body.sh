#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)

for case_name in unit1_28mm unit2_70mm; do
  arch -x86_64 lldb -s \
    "$ROOT/tools/lldb_probes/distortion_table/$case_name.lldb" \
    "$ROOT/tools/lri_process" \
    >"$ROOT/runs/distortion_table/$case_name.log" 2>&1
  sleep 20
done
