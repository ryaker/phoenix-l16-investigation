#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_node_dest_sentinel_custody"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.lldb" "$ROOT/tools/lri_process" > "$OUT/node_dest_sentinel_custody_28mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.lldb" "$ROOT/tools/lri_process" > "$OUT/node_dest_sentinel_custody_35mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.lldb" "$ROOT/tools/lri_process" > "$OUT/node_dest_sentinel_custody_70mm.log" 2>&1
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.lldb" "$ROOT/tools/lri_process" > "$OUT/node_dest_sentinel_custody_150mm.log" 2>&1

python3 "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_sentinel_custody.py"
