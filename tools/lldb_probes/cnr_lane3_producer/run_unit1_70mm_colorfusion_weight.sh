#!/usr/bin/env bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
exec arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/cnr_lane3_producer/unit1_70mm_colorfusion_weight.lldb"
