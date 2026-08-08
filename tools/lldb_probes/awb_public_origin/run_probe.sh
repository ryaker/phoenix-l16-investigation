#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
RUNS="$ROOT/runs/awb_public_origin"
mkdir -p "$RUNS"

for name in unit1_28mm unit1_35mm unit1_70mm unit1_150mm unit2_28mm; do
  sleep 20
  rm -f "$RUNS/$name.hdr"
  arch -x86_64 lldb -b \
    -s "$ROOT/tools/lldb_probes/awb_public_origin/$name.lldb" \
    >"$RUNS/$name.log" 2>&1
done

exec python3 "$ROOT/tools/lldb_probes/awb_public_origin/verify_awb_public_origin.py" \
  --require-runtime \
  --json-out "$RUNS/verification.json"
