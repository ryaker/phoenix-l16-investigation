#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"

mkdir -p "$ROOT/runs/prefusion_state5_acceptance_path"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_state5_acceptance_path/state5_acceptance_70mm.lldb" > "$ROOT/runs/prefusion_state5_acceptance_path/state5_acceptance_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_state5_acceptance_path/state5_acceptance_150mm.lldb" > "$ROOT/runs/prefusion_state5_acceptance_path/state5_acceptance_150mm.log" 2>&1
