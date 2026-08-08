#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/index5_composed_geometry_origin"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/index5_composed_geometry_origin/composed_geometry_unit2_28mm.lldb" > "$OUT/composed_geometry_unit2_28mm.log"
