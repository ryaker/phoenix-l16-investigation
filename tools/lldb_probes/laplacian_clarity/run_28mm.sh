#!/bin/sh
set -eu

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/laplacian_clarity/laplacian_clarity_28mm.lldb"
bash "$ROOT/tools/lldb_probes/laplacian_clarity/run_unused_config_fields_28mm.sh"
python3 "$ROOT/tools/lldb_probes/laplacian_clarity/verify_laplacian_clarity.py"
