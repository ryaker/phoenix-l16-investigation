#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_26d750_source_range_builder/source_range_${tier}.lldb"
done
