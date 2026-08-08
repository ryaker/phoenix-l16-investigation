#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
cleanup() {
  rm -f /private/tmp/g49_refinement_28mm.hdr \
    /private/tmp/g49_refinement_35mm.hdr \
    /private/tmp/g49_refinement_70mm.hdr \
    /private/tmp/g49_refinement_150mm.hdr
}
trap cleanup EXIT
for zoom in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/g49_subpixel_refinement/refinement_${zoom}.lldb"
done
