#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_opus_index5_origin_classification"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_28mm.lldb" > "$OUT/index5_origin_28mm.log"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_35mm.lldb" > "$OUT/index5_origin_35mm.log"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_70mm.lldb" > "$OUT/index5_origin_70mm.log"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_150mm.lldb" > "$OUT/index5_origin_150mm.log"
