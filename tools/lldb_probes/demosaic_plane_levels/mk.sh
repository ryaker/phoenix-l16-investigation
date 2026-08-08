#!/bin/zsh
# Generate + run one .lldb per canonical shot for the demosaic plane-level probe.
set -u
FW=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
RE=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
D=$RE/tools/lldb_probes/demosaic_plane_levels
OUT=$RE/runs/demosaic_plane_levels
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
  [[ -f "$p" ]] || { echo "MISSING $n"; continue; }
  cat > "$OUT/$n.lldb" <<EOF
command script import $D/probe.py
script probe.reset("$n demosaic plane levels")
settings set target.env-vars DYLD_FRAMEWORK_PATH=$FW DYLD_LIBRARY_PATH=$FW
target create $RE/tools/lri_process
breakpoint set --shlib libcp.dylib --address 0x2eb560
breakpoint command add 1 -s python -o "probe.hit(frame, bp_loc, internal_dict)"
process launch -- "$p" "$OUT/$n.hdr" --profile 3 --export-fmt 3
script probe.report()
quit
EOF
  echo "=== $n ==="
  arch -x86_64 lldb -b -s "$OUT/$n.lldb" > "$OUT/$n.log" 2>&1
  echo "  rc=$?"
  sed -n '/L16_DPL_BEGIN/,/L16_DPL_END/p' "$OUT/$n.log"
done
echo ALLDONE
