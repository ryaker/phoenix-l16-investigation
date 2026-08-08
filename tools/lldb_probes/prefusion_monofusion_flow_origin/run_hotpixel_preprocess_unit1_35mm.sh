#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export HOTPIXEL_OUT="$ROOT/runs/prefusion_monofusion_flow_origin/unit1_35mm_hotpixel_preprocess"
export HOTPIXEL_LABEL="Unit-1 canonical-35mm A2 MonoFusion hot-pixel preprocessing"
export HOTPIXEL_LRI="/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
exec bash "$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/run_hotpixel_preprocess_unit1_28mm.sh"
