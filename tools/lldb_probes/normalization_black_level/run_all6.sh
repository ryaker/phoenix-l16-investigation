#!/usr/bin/env bash
# Corpus-wide black-level solver capture (both bodies, four focals).
set -uo pipefail
ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
R="$ROOT/tools/lldb_probes/normalization_black_level/run_black6.sh"

run() { bash "$R" "$2" "$1" || echo "FAIL $1"; }

run u1_28   "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
run u1_35   "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
run u1_70   "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
run u1_150  "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
run u2_35   "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"
run u1g_35  "/Volumes/Base Photos/Light/2018-07-04/L16_01485.lri"
run u2n1_35 "/Volumes/Base Photos/Light/2018-07-02/L16_02020.lri"
run u2_28   "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"
echo ALL6DONE
