#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_helpers_23c5f0_f33d0_runtime

arch -x86_64 lldb -b -s tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_28mm.lldb > runs/state_helpers_23c5f0_f33d0_runtime/state_helper_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_35mm.lldb > runs/state_helpers_23c5f0_f33d0_runtime/state_helper_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_70mm.lldb > runs/state_helpers_23c5f0_f33d0_runtime/state_helper_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_150mm.lldb > runs/state_helpers_23c5f0_f33d0_runtime/state_helper_150mm.log
