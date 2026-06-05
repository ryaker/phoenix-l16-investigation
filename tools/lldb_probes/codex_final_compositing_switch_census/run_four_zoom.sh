#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_final_compositing_switch_census

arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_switch_census/switch_census_28mm.lldb > runs/codex_final_compositing_switch_census/switch_census_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_switch_census/switch_census_35mm.lldb > runs/codex_final_compositing_switch_census/switch_census_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_switch_census/switch_census_70mm.lldb > runs/codex_final_compositing_switch_census/switch_census_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_switch_census/switch_census_150mm.lldb > runs/codex_final_compositing_switch_census/switch_census_150mm.log
