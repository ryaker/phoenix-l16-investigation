#!/bin/sh
set -eu

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PROBE=$ROOT/tools/lldb_probes/lri_consumed_block_roles
RUNS=$ROOT/runs/lri_consumed_block_roles

mkdir -p "$RUNS"
for tier in 28 35 70 150; do
  arch -x86_64 lldb -b -s "$PROBE/unit1_${tier}mm.lldb" \
    >"$RUNS/unit1_${tier}mm.log" 2>&1
  rm -f "$RUNS/unit1_${tier}mm.hdr"
done
