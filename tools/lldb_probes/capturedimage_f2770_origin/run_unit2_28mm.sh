#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/capturedimage_f2770_origin

arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_unit2_28mm.lldb
