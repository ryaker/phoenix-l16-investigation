#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/cnr_lane3_producer/fusioncache_tuning"
mkdir -p "$OUT"

run_one() {
  local label="$1"
  local slug="$2"
  local lri="$3"
  local script="$OUT/$slug.lldb"

  rm -f "$OUT/$slug.json"
  sed \
    -e "s|@@LABEL@@|$label|g" \
    -e "s|@@OUTPUT@@|$OUT/$slug.json|g" \
    -e "s|@@LRI@@|$lri|g" \
    "$ROOT/tools/lldb_probes/cnr_lane3_producer/fusioncache_tuning_template.lldb" \
    > "$script"
  arch -x86_64 lldb -b -s "$script"
}

run_one "Unit-1 28mm" unit1_28mm "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
run_one "Unit-1 35mm" unit1_35mm "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
run_one "Unit-1 70mm" unit1_70mm "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
run_one "Unit-1 150mm" unit1_150mm "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
run_one "Unit-2 28mm" unit2_28mm "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"
run_one "Unit-2 70mm" unit2_70mm "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"
