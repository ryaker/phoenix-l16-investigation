#!/bin/zsh
# Per-module sensor_exposure / sensor_analog_gain / digital_gain for each shot in
# the verification corpus.  Tests whether Phoenix's per-shot achromatic gain gap
# vs the Lumen master tracks a contributor-vs-anchor exposure imbalance.
set -u
RE=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
OUT=$RE/runs/verify_master
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
  n=$NAMES[$i]
  python3 "$RE/tools/lri_field_inspect.py" --lri "$PATHS[$i]" --block-index 0 \
     --proto-class LightHeader --depth 3 --json > "$OUT/${n}_hdr.json" 2>"$OUT/${n}_hdr.err"
  echo "$n rc=$? bytes=$(stat -f%z "$OUT/${n}_hdr.json")"
done
echo DONE
