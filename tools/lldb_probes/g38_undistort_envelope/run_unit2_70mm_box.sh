#!/usr/bin/env bash
set -euo pipefail

cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering
mkdir -p runs/g38_undistort_envelope
arch -x86_64 lldb -b -s \
  tools/lldb_probes/g38_undistort_envelope/unit2_70mm_box.lldb \
  > runs/g38_undistort_envelope/unit2_70mm_box.log
rm -f /private/tmp/g38_unit2_70mm.jpg
