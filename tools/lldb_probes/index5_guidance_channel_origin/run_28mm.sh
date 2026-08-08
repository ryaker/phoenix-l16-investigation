#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/index5_guidance_channel_origin/guidance_origin_28mm.lldb"
