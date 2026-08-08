#!/bin/sh
set -eu
ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
SOURCE="/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
STAGED=/Users/ryaker/L16_02130_nlm_topology.lri
OUTPUT=/Users/ryaker/nlm_topology_28mm.hdr
mkdir -p "$ROOT/runs/nlm_topology_boundary"
if [ ! -f "$STAGED" ] || [ "$(stat -f %z "$STAGED")" != "$(stat -f %z "$SOURCE")" ]; then
  cp "$SOURCE" "$STAGED"
fi
trap 'rm -f "$STAGED" "$OUTPUT"' EXIT
arch -x86_64 lldb -s "$ROOT/tools/lldb_probes/nlm_topology_boundary/unit1_28mm.lldb" \
  /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process \
  > "$ROOT/runs/nlm_topology_boundary/unit1_28mm.log" 2>&1
if [ -f "$OUTPUT" ]; then
  mv "$OUTPUT" "$ROOT/runs/nlm_topology_boundary/unit1_28mm.hdr"
fi
