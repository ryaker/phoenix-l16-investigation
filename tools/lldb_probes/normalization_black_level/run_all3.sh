#!/usr/bin/env bash
D="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/normalization_black_level"
run() { bash "$D/run_black3.sh" "$1" "$2" || echo "FAIL $2"; }
run "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri" u2_35
run "/Volumes/Base Photos/Light/2018-07-02/L16_02020.lri" u2n1_35
run "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri" u1_35
run "/Volumes/Base Photos/Light/2018-07-04/L16_01485.lri" u1g_35
run "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" u1_28
run "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri" u2_28
run "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri" u1_70
run "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri" u1_150
echo ALL3DONE
