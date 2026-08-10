#!/usr/bin/env bash
# Side-by-side plane comparison across focals and both bodies.
# For each labeled LRI: (1) run the installed Lumen deterministic capture FRESH,
# (2) run Phoenix FRESH on the SAME LRI, (3) compare all 5 stereo Images[].
# Both sides generated this session from one input -- no cached data, no cross
# build/LRI confounds. Prints a corr/slope table per plane.
#
# usage: sidebyside_matrix.sh [PHX_ENVCATMULL]   # arg1 non-empty -> Catmull-Rom
set -uo pipefail
ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
PHX=/Users/ryaker/L16_Phoenix/phoenix/build/tools/phoenix_depth_tool
CAP=$ROOT/tools/lldb_probes/index5_nondeterminism/run_g42_bank_capture.sh
KERNEL="${1:-}"   # empty=bilinear(default); non-empty sets PHX_ENVCATMULL=1
OUTROOT=/tmp/sxs_matrix
mkdir -p "$OUTROOT"

# label:lri  (all verified tier/focal via PHX_CALIBDUMP 2026-08-10)
FRAMES=(
  "u1_28:/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
  "u1_35:/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
  "u1_70:/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
  "u1_150:/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
  "u2_28:/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"
  "u2_35:/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"
  "u2_70:/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri"
)

for entry in "${FRAMES[@]}"; do
  label="${entry%%:*}"; lri="${entry#*:}"
  [[ -f "$lri" ]] || { echo "$label MISSING $lri"; continue; }
  echo "===== $label ====="
  # (1) Lumen fresh
  lumdir="$ROOT/runs/index5_nondeterminism/sxs_${label}"
  rm -rf "$lumdir"
  "$CAP" "$lri" "sxs_${label}" default serial-executor-2d30 > "$OUTROOT/${label}_lumen.log" 2>&1
  # (2) Phoenix fresh
  phxdir="$OUTROOT/${label}_phx"; mkdir -p "$phxdir/dumps"
  env ${KERNEL:+PHX_ENVCATMULL=1} PHX_DUMPSRC="$phxdir/dumps" \
    "$PHX" "$lri" "$phxdir/out" --pyramid on --maxlevel 0 > "$OUTROOT/${label}_phx.log" 2>&1
  # (3) compare
  python3 - "$lumdir" "$phxdir/dumps" "$label" "${KERNEL:+catmull}${KERNEL:-bilinear}" <<'PY'
import sys, glob, numpy as np
lumdir, phxdir, label, kern = sys.argv[1:5]
def load(p): return np.frombuffer(open(p,'rb').read(),np.uint8).reshape(-1,4).astype(np.float64)
for i in range(5):
    lp=f"{lumdir}/image{i}.rgba8"
    pg=glob.glob(f"{phxdir}/phx_src_image{i}_*.rgba8")
    try:
        L=load(lp); P=load(pg[0])
    except Exception as e:
        print(f"  {label} img{i}: MISSING ({e})"); continue
    n=min(len(L),len(P)); idx=np.arange(0,n,17)
    outs=[]
    for ch,nm in enumerate('RGB'):
        x=P[idx,ch]; y=L[idx,ch]
        if x.std()<1e-6: outs.append(f"{nm}=const"); continue
        outs.append(f"{nm} {np.corrcoef(x,y)[0,1]:.4f}/{np.polyfit(x,y,1)[0]:.3f}")
    print(f"  {label} img{i} [{kern}] " + "  ".join(outs))
PY
done
echo "MATRIX DONE"
