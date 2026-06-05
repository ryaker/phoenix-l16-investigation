#!/usr/bin/env bash
set -euo pipefail

cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_opus_w5_magnitude_repro

arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_w5_magnitude_repro/score_nonzero_35mm.lldb > runs/codex_opus_w5_magnitude_repro/score_nonzero_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_opus_w5_magnitude_repro/score_nonzero_70mm.lldb > runs/codex_opus_w5_magnitude_repro/score_nonzero_70mm.log
