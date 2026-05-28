#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p runs/c6_route_census_unprobed_direct

scripts=(
  tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_a.lldb
  tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_b.lldb
  tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_a.lldb
  tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_b.lldb
)

for script in "${scripts[@]}"; do
  stem="$(basename "$script" .lldb)"
  log="runs/c6_route_census_unprobed_direct/${stem}.log"
  echo "RUN $script"
  arch -x86_64 lldb -b -s "$script" > "$log" 2>&1
  echo "DONE $script -> $log"
done
