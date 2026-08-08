#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
DIR="$ROOT/tools/lldb_probes/lri_firing_set_census"
RUN="$ROOT/runs/lri_firing_set_census"
mkdir -p "$RUN"

for case in unit1_28mm_tele unit2_28mm_tele unit2_74mm_wide; do
  arch -x86_64 lldb -b -s "$DIR/variant_route_${case}.lldb" \
    > "$RUN/variant_route_${case}.log" 2>&1
done

python3 "$DIR/verify_variant_routes.py"
