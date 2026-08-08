#!/bin/bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/type1_28mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/type2_28mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/brush_type1_28mm.lldb"
python3 "$ROOT/tools/lldb_probes/editor_render_type_topology/verify_editor_render_type_topology.py"
