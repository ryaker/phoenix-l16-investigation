#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/codex_1f0ce0_k_source_trace

arch -x86_64 lldb -b -s tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_28mm.lldb > runs/codex_1f0ce0_k_source_trace/k_source_trace_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_35mm.lldb > runs/codex_1f0ce0_k_source_trace/k_source_trace_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_70mm.lldb > runs/codex_1f0ce0_k_source_trace/k_source_trace_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_150mm.lldb > runs/codex_1f0ce0_k_source_trace/k_source_trace_150mm.log
