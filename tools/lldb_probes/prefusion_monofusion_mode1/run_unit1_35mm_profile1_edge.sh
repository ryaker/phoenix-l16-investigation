#!/bin/sh
set -eu

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
INPUT="/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"

dd if="$INPUT" of=/dev/null bs=4096 count=1 2>/dev/null
sleep 2
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_monofusion_mode1/unit1_35mm_profile1_edge.lldb"
