#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
DIR="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$DIR/parent_decision_${tier}.lldb"
done

arch -x86_64 lldb -b -s "$DIR/parent_decision_unit2_35mm.lldb"

python3 "$DIR/verify_216f60_parent_decision.py"
