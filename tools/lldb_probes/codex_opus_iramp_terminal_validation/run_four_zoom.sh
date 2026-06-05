#!/usr/bin/env bash
set -euo pipefail

cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_opus_iramp_terminal_validation

arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_28mm.lldb > runs/codex_opus_iramp_terminal_validation/iramp_terminal_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_35mm.lldb > runs/codex_opus_iramp_terminal_validation/iramp_terminal_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_70mm.lldb > runs/codex_opus_iramp_terminal_validation/iramp_terminal_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_150mm.lldb > runs/codex_opus_iramp_terminal_validation/iramp_terminal_150mm.log
