#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"

mkdir -p "$ROOT/runs/prefusion_promoted_record_watch"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_promoted_record_watch/promoted_watch_70mm.lldb" > "$ROOT/runs/prefusion_promoted_record_watch/promoted_watch_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_promoted_record_watch/promoted_watch_150mm.lldb" > "$ROOT/runs/prefusion_promoted_record_watch/promoted_watch_150mm.log" 2>&1
