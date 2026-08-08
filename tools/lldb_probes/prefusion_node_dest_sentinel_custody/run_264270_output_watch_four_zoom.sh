#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
DIR="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$DIR/output_watch_${tier}.lldb"
done

python3 "$DIR/verify_264270_output_watch.py"
