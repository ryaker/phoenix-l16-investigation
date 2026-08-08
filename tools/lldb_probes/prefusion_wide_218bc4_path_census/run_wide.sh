#!/bin/sh
set -eu

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_wide_218bc4_path_census"
LLDB_DIR="$ROOT/tools/lldb_probes/prefusion_wide_218bc4_path_census"
TARGET="/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process"

mkdir -p "$OUT"
arch -x86_64 lldb -b -s "$LLDB_DIR/wide_28mm.lldb" "$TARGET" > "$OUT/wide_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$LLDB_DIR/wide_35mm.lldb" "$TARGET" > "$OUT/wide_35mm.log" 2>&1
python3 "$LLDB_DIR/verify_wide_path_census.py"
