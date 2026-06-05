#!/usr/bin/env bash
set -euo pipefail

cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_iramp_sentinel_gate_validation

arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_28mm.lldb > runs/codex_iramp_sentinel_gate_validation/sentinel_gate_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_35mm.lldb > runs/codex_iramp_sentinel_gate_validation/sentinel_gate_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_70mm.lldb > runs/codex_iramp_sentinel_gate_validation/sentinel_gate_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_150mm.lldb > runs/codex_iramp_sentinel_gate_validation/sentinel_gate_150mm.log
