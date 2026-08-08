#!/bin/bash
set -euo pipefail
cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering
mkdir -p runs/g43_direction_vectors
arch -x86_64 lldb -b -s tools/lldb_probes/g43_direction_vectors/g43_spatial_pos_35mm.lldb \
  > runs/g43_direction_vectors/g43_spatial_pos_35mm.log 2>&1
