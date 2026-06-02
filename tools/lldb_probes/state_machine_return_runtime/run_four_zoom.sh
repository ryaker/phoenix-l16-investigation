#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

arch -x86_64 lldb -b -s tools/lldb_probes/state_machine_return_runtime/state_machine_return_28mm.lldb > runs/state_machine_return_runtime/state_machine_return_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_machine_return_runtime/state_machine_return_35mm.lldb > runs/state_machine_return_runtime/state_machine_return_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_machine_return_runtime/state_machine_return_70mm.lldb > runs/state_machine_return_runtime/state_machine_return_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_machine_return_runtime/state_machine_return_150mm.lldb > runs/state_machine_return_runtime/state_machine_return_150mm.log
