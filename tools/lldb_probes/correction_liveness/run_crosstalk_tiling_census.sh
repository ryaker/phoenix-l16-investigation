#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 SOURCE_LRI LABEL [CAMERA_KEY]" >&2
  exit 2
fi

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
SOURCE="$1"
LABEL="$2"
CAMERA_KEY="${3:-0}"
OUT="$ROOT/runs/correction_liveness/tiling_$LABEL"
STAGED="$OUT/camera_${CAMERA_KEY}.lri"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json" "$LOG" "$SCRIPT"
if [[ "${REUSE_STAGED:-0}" != "1" || ! -s "$STAGED" ]]; then
  python3 "$ROOT/tools/lldb_probes/index5_guidance_channel_origin/stage_single_camera_lri.py" \
    "$SOURCE" "$STAGED" --camera-key "$CAMERA_KEY" > "$OUT/staging.json"
fi

python3 - "$ROOT" "$LABEL" "$OUT" "$STAGED" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

root, label, output, staged, script = sys.argv[1:]
commands = [
    f"command script import {root}/tools/lldb_probes/correction_liveness/crosstalk_tiling_census_probe.py",
    f"script crosstalk_tiling_census_probe.reset({json.dumps(label)}, {json.dumps(output)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib lri_process --name main",
    "process launch -- " + json.dumps(staged) + " " +
    json.dumps(str(Path(output) / "output.hdr")) + " --profile 3 --export-fmt 3 --no-auto-lris",
    "script crosstalk_tiling_census_probe.install(lldb.debugger)",
    "breakpoint delete 1",
    "process continue",
    f"script crosstalk_tiling_census_probe.write_report({json.dumps(str(Path(output) / 'report.json'))})",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1 || true
tail -20 "$LOG"
test -s "$OUT/report.json"
