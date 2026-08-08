#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
DIR="$ROOT/tools/lldb_probes/prefusion_wide_minimum_selector"

cd "$ROOT"
arch -x86_64 lldb -b -s "$DIR/wide_minimum_selector_28mm.lldb"
python3 "$DIR/verify_wide_minimum_selector.py"
