#!/bin/zsh
# Two-body x four-focal master verification sweep.
# For each canonical LRI: render Lumen profile-3 fmt-3 HDR master and the
# Phoenix master, then compare chroma with hdrstat.py.
set -u
LUMEN_FW=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
RE=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
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

for i in {1..5}; do
  n=$NAMES[$i]; p=$PATHS[$i]
  if [[ ! -f "$p" ]]; then echo "MISSING $n: $p"; continue; fi

  if [[ ! -s "$OUT/${n}_lumen.hdr" ]]; then
    echo "=== lumen $n ==="
    DYLD_FRAMEWORK_PATH=$LUMEN_FW DYLD_LIBRARY_PATH=$LUMEN_FW \
      arch -x86_64 "$RE/tools/lri_process" "$p" "$OUT/${n}_lumen.hdr" \
      --profile 3 --export-fmt 3 > "$OUT/${n}_lumen.log" 2>&1
    echo "  rc=$? size=$(stat -f%z "$OUT/${n}_lumen.hdr" 2>/dev/null)"
  fi

  if [[ ! -s "$OUT/${n}_phx.hdr" ]]; then
    echo "=== phoenix $n ==="
    "$PHX" "$p" -o "$OUT/${n}_phx.hdr" > "$OUT/${n}_phx.log" 2>&1
    echo "  rc=$? size=$(stat -f%z "$OUT/${n}_phx.hdr" 2>/dev/null)"
  fi
done
echo "DONE"
