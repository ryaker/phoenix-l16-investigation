#!/bin/zsh
set -euo pipefail

repo=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
probe=$repo/tools/lldb_probes/prefusion_monofusion_mode_selector

cd "$repo"
for profile in 0 1 2 3; do
  arch -x86_64 lldb -s "$probe/profile${profile}.lldb"
done
