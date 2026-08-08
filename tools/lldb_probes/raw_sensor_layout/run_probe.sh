#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
mkdir -p "$ROOT/runs/raw_sensor_layout"
rm -f "$ROOT"/runs/raw_sensor_layout/runtime_*.json

stage_input() {
  source_path=$1
  staged_path=$2
  source_size=$(stat -f %z "$source_path")
  staged_size=$(stat -f %z "$staged_path" 2>/dev/null || printf 0)
  if [ "$source_size" != "$staged_size" ]; then
    cp -p "$source_path" "$staged_path"
  fi
}

stage_input "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  "$ROOT/runs/raw_sensor_layout/input_unit1_28mm.lri"

# A prior debugger-killed render can leave renderer process state unsettled.
# A normal priming render plus a teardown interval makes the stopped-frame
# observation reproducible without broadening this static/body-independent claim.
arch -x86_64 "$ROOT/tools/lri_process" \
  "$ROOT/runs/raw_sensor_layout/input_unit1_28mm.lri" \
  "$ROOT/runs/raw_sensor_layout/prime.jpg" \
  --profile 3 --export-fmt 4 --no-auto-lris >/dev/null
sleep 15
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/raw_sensor_layout/unit1_28mm.lldb"

exec python3 "$ROOT/tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py" \
  --require-runtime \
  --json-out "$ROOT/runs/raw_sensor_layout/verification.json"
