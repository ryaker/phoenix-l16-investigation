#!/bin/bash
set -euo pipefail
cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering
arch -x86_64 lldb -b -s tools/lldb_probes/g43_g40_census/census_35mm.lldb \
  /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process \
  > runs/g43_g40_census/census_35mm.log 2>&1
