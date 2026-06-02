#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_helper_f34e0_match_runtime

arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_28mm.lldb > runs/state_helper_f34e0_match_runtime/f34e0_match_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_35mm.lldb > runs/state_helper_f34e0_match_runtime/f34e0_match_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_70mm.lldb > runs/state_helper_f34e0_match_runtime/f34e0_match_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_150mm.lldb > runs/state_helper_f34e0_match_runtime/f34e0_match_150mm.log
