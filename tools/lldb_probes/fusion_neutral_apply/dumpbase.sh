#!/bin/zsh
# Merge-isolation experiment: PHX_DUMPBASE writes the anchor/base canvas straight
# through square + AWB + CCM with NO tier crop and NO merge, then returns.
# Comparing {n}_base.hdr against {n}_lumen.hdr isolates whether the per-shot
# achromatic gain (phx/lumen 0.70-1.37) is introduced by the merge or upstream.
set -u
RE=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
PHX=/Users/ryaker/L16_Phoenix/phoenix/build/tools/phoenix_fuse
OUT=$RE/runs/verify_master
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

for i in {1..5}; do
  n=$NAMES[$i]; p=$PATHS[$i]
  if [[ ! -f "$p" ]]; then echo "MISSING $n: $p"; continue; fi
  echo "=== $n ==="
  PHX_DBG=1 PHX_DUMPBASE="$OUT/${n}_base.hdr" \
    "$PHX" "$p" -o /tmp/${n}_ignored.hdr > "$OUT/${n}_base.log" 2>&1
  echo "  rc=$? size=$(stat -f%z "$OUT/${n}_base.hdr" 2>/dev/null)"
  grep -E '^\[(dump|DBG|awb )' "$OUT/${n}_base.log"
done
echo "DONE"
