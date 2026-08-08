#!/bin/sh
set -eu

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/laplacian_clarity/unused_config_fields_a_28mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/laplacian_clarity/unused_config_fields_b_28mm.lldb"
