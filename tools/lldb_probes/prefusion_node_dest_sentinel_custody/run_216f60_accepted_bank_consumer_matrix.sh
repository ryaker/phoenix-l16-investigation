#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
DIR="$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody"

for tier in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$DIR/accepted_bank_consumer_${tier}.lldb"
done

arch -x86_64 lldb -b -s "$DIR/accepted_bank_consumer_unit2_35mm.lldb"

python3 "$DIR/verify_216f60_accepted_bank_consumer.py"
