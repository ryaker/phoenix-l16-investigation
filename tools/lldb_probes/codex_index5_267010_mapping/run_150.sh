#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_index5_267010_mapping"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_index5_267010_mapping/index5_mapping_150mm.lldb" > "$OUT/index5_mapping_150mm.log"
