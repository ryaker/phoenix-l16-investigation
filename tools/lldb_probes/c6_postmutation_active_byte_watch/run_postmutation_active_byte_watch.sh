#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p runs/c6_postmutation_active_byte_watch

scripts=(
  tools/lldb_probes/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_70mm.lldb
  tools/lldb_probes/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_150mm.lldb
)

for script in "${scripts[@]}"; do
  stem="$(basename "$script" .lldb)"
  log="runs/c6_postmutation_active_byte_watch/${stem}.log"
  echo "RUN $script"
  arch -x86_64 lldb -b -s "$script" > "$log" 2>&1
  echo "DONE $script -> $log"
done
