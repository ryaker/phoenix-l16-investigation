#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_${tier}.lldb"
done
