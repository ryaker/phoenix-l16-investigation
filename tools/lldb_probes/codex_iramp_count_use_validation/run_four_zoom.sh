#!/usr/bin/env bash
set -euo pipefail

cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_iramp_count_use_validation

arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_28mm.lldb > runs/codex_iramp_count_use_validation/iramp_count_use_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_35mm.lldb > runs/codex_iramp_count_use_validation/iramp_count_use_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_70mm.lldb > runs/codex_iramp_count_use_validation/iramp_count_use_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_150mm.lldb > runs/codex_iramp_count_use_validation/iramp_count_use_150mm.log
