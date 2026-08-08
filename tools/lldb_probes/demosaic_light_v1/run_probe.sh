#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
mkdir -p "$ROOT/runs/demosaic_light_v1"

arch -x86_64 "$ROOT/tools/lri_process" \
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  "$ROOT/runs/demosaic_light_v1/prime.hdr" >/dev/null
sleep 15

arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/demosaic_light_v1/unit1_28mm.lldb"

arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/demosaic_light_v1/guide_unit1_28mm.lldb"

exec python3 "$ROOT/tools/lldb_probes/demosaic_light_v1/verify_demosaic_light_v1.py" \
  --require-runtime \
  --json-out "$ROOT/runs/demosaic_light_v1/verification.json"
