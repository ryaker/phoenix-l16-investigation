#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_lookup_endpoint_count_origin"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_${tier}.lldb" > "$OUT/endpoint_count_origin_${tier}.log"
done
