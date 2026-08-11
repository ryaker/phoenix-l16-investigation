#!/usr/bin/env bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)

"$HERE/run_one.sh" \
  unit1_28mm \
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  /tmp/cf_selection_unit1_28mm.hdr

"$HERE/run_one.sh" \
  unit2_70mm \
  "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri" \
  /tmp/cf_selection_unit2_70mm.hdr

