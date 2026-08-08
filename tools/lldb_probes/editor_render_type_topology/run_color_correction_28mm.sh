#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
exec arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/editor_render_type_topology/color_correction_runtime_28mm.lldb"
