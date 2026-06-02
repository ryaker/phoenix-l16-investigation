#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"

mkdir -p "$ROOT/runs/prefusion_state5_later_watch"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_state5_later_watch/state5_later_70mm.lldb" > "$ROOT/runs/prefusion_state5_later_watch/state5_later_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_state5_later_watch/state5_later_150mm.lldb" > "$ROOT/runs/prefusion_state5_later_watch/state5_later_150mm.log" 2>&1
