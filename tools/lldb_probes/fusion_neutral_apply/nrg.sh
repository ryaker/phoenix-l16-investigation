#!/bin/zsh
# Per-module exposure-energy census for the five canonical shots.
# Only the early [nrg]/[mono] prints are needed, so each run is killed once
# the plane build starts.
set -u
PHX=/Users/ryaker/L16_Phoenix/phoenix/build/tools/phoenix_fuse
OUT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master
mkdir -p "$OUT"
typeset -a NAMES PATHS
NAMES=(u1_28 u1_35 u1_70 u1_150 u2_35)
PATHS=(
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
  "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
  "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
  "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
  "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"
)
: > "$OUT/nrg.log"
for i in {1..5}; do
  n=$NAMES[$i]; p=$PATHS[$i]
  echo "=== $n ===" >> "$OUT/nrg.log"
  "$PHX" "$p" -o /tmp/${n}_nrg.hdr > /tmp/${n}_nrg.txt 2>&1 &
  pid=$!
  for t in {1..40}; do
    sleep 1
    if grep -q '^\[demo\] anchor' /tmp/${n}_nrg.txt 2>/dev/null; then break; fi
  done
  kill -9 $pid 2>/dev/null
  wait $pid 2>/dev/null
  grep -E '^\[(nrg |mono|demo|tier|canv)' /tmp/${n}_nrg.txt >> "$OUT/nrg.log"
done
echo ALLDONE
