#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_299c70_source_index_producer"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_source_index_producer/source_index_150mm.lldb" > "$OUT/source_index_150mm.log"
