#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
mkdir -p "$ROOT/runs/prefusion_monofusion_mode0_tile/unit1_28mm"
arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/prefusion_monofusion_mode0_tile/unit1_28mm.lldb"
