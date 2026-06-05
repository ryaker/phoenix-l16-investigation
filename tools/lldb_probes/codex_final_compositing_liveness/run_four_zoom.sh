#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_final_compositing_liveness

arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_liveness/final_compositing_28mm.lldb > runs/codex_final_compositing_liveness/final_compositing_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_liveness/final_compositing_35mm.lldb > runs/codex_final_compositing_liveness/final_compositing_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_liveness/final_compositing_70mm.lldb > runs/codex_final_compositing_liveness/final_compositing_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_liveness/final_compositing_150mm.lldb > runs/codex_final_compositing_liveness/final_compositing_150mm.log
