#!/bin/zsh
set -euo pipefail

repo=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
probe=$repo/tools/lldb_probes/final_iramp_image_effect

cd "$repo"
arch -x86_64 lldb -s "$probe/baseline_35mm_a.lldb"
arch -x86_64 lldb -s "$probe/baseline_35mm_b.lldb"
arch -x86_64 lldb -s "$probe/zero_score_35mm.lldb"
arch -x86_64 lldb -s "$probe/baseline_70mm_a.lldb"
arch -x86_64 lldb -s "$probe/baseline_70mm_b.lldb"
arch -x86_64 lldb -s "$probe/zero_score_70mm.lldb"
arch -x86_64 lldb -s "$probe/zero_score_70mm_b.lldb"
python3 "$probe/verify_final_iramp_image_effect.py"
