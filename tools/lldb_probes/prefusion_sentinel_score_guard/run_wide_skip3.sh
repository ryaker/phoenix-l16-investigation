#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/prefusion_sentinel_score_guard"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.lldb" > "$OUT/sentinel_score_guard_28mm_skip3.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.lldb" > "$OUT/sentinel_score_guard_35mm_skip3.log" 2>&1
