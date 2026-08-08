#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering
mkdir -p runs/prefusion_terminal_two_pass_calib_consumer

arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/unit1_35mm.lldb \
  > runs/prefusion_terminal_two_pass_calib_consumer/unit1_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/unit2_35mm.lldb \
  > runs/prefusion_terminal_two_pass_calib_consumer/unit2_35mm.log

python3 tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/verify_two_pass.py
