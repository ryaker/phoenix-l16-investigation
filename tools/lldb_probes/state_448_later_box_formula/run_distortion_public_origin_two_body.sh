#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_448_distortion_public_origin

arch -x86_64 lldb -b -s \
  tools/lldb_probes/state_448_later_box_formula/distortion_public_origin_unit1_28mm.lldb \
  > runs/state_448_distortion_public_origin/unit1_28mm.log
arch -x86_64 lldb -b -s \
  tools/lldb_probes/state_448_later_box_formula/distortion_public_origin_unit2_70mm.lldb \
  > runs/state_448_distortion_public_origin/unit2_70mm.log
