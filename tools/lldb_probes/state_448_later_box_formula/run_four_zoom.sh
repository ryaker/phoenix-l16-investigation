#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_448_later_box_formula

arch -x86_64 lldb -b -s tools/lldb_probes/state_448_later_box_formula/box_formula_28mm.lldb > runs/state_448_later_box_formula/box_formula_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_later_box_formula/box_formula_35mm.lldb > runs/state_448_later_box_formula/box_formula_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_later_box_formula/box_formula_70mm.lldb > runs/state_448_later_box_formula/box_formula_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_later_box_formula/box_formula_150mm.lldb > runs/state_448_later_box_formula/box_formula_150mm.log
