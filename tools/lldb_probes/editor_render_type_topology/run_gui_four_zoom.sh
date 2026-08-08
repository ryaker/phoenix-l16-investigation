#!/bin/bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/brush_type1_28mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/gui_type1_35mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/gui_type1_70mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/editor_render_type_topology/gui_type1_150mm.lldb"
python3 "$ROOT/tools/lldb_probes/editor_render_type_topology/verify_editor_render_type_topology.py"
python3 "$ROOT/tools/lldb_probes/editor_render_type_topology/verify_lumen_editor_callgraph.py"
