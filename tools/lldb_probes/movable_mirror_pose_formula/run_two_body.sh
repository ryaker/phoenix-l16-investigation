#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/movable_mirror_pose_formula"
mkdir -p "$OUT"

for sample in unit1_28mm unit1_35mm unit1_70mm unit1_150mm unit2_70mm; do
  arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/movable_mirror_pose_formula/${sample}.lldb" > "$OUT/${sample}.log"
done
