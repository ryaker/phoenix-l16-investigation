#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_index5_lookup_vector_public_origin"
mkdir -p "$OUT"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_${tier}.lldb" > "$OUT/lookup_vector_public_${tier}.log"
done
