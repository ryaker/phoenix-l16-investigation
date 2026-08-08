#!/bin/zsh
# Log-only pass: re-render each canonical LRI with the rebuilt phoenix_fuse so
# the "[awb ] supplied awb_rgb" line is captured per shot.
set -u
PHX=/Users/ryaker/L16_Phoenix/phoenix/build/tools/phoenix_fuse
OUT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master
typeset -a NAMES PATHS
NAMES=(u1_28 u1_35 u1_70 u1_150 u2_35)
PATHS=(
  "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
  "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
  "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
  "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
  "/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"
)
for i in {1..5}; do
  n=$NAMES[$i]; p=$PATHS[$i]
  echo "=== $n ==="
  "$PHX" "$p" -o /tmp/awbprobe_$n.hdr > "$OUT/${n}_phx.log" 2>&1
  grep "\[awb \]" "$OUT/${n}_phx.log"
  rm -f /tmp/awbprobe_$n.hdr
done
echo DONE
