#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/index5_plane_sweep_correspondence/unit1_28mm"
mkdir -p "$OUT"
cp -p "$ROOT/tools/lri_process" /private/tmp/lri_process_index5_correspondence
test "$(shasum -a 256 /private/tmp/lri_process_index5_correspondence | cut -d' ' -f1)" = \
  "f3cc0f481192a24289ffba4dbe5a28dfac711673821bf1f6715f0bfcd5f9bedf"
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/index5_plane_sweep_correspondence/plane_sweep_28mm.lldb" \
  > "$OUT/run.log"
