#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/prefusion_20ca00_copied_sentinel_gate"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_150mm.lldb" > "$OUT/copied_sentinel_gate_150mm.log" 2>&1
