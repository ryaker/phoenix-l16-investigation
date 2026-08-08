#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
cleanup() {
  rm -f /private/tmp/g40_hypothesis_28mm.hdr \
    /private/tmp/g40_hypothesis_35mm.hdr \
    /private/tmp/g40_hypothesis_70mm.hdr \
    /private/tmp/g40_hypothesis_150mm.hdr
}
trap cleanup EXIT
for zoom in 28mm 35mm 70mm 150mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/g40_hypothesis_policy/hypothesis_${zoom}.lldb"
  rm -f "/private/tmp/g40_hypothesis_${zoom}.hdr"
done
