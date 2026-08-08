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
OUT="$ROOT/runs/create_stereo_color_public_reconstruction/$LABEL"
STAGED="$OUT/camera_${CAMERA_KEY}.lri"
SCRIPT="$OUT/capture.lldb"
REPORT="$OUT/report.json"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$REPORT" "$LOG" "$SCRIPT"
if [[ "${REUSE_STAGED:-0}" != "1" ]]; then
  python3 "$ROOT/tools/lldb_probes/index5_guidance_channel_origin/stage_single_camera_lri.py" \
    "$SOURCE" "$STAGED" --camera-key "$CAMERA_KEY" > "$OUT/staging.json"
else
  test -s "$STAGED"
fi

python3 - "$ROOT" "$LABEL" "$OUT" "$STAGED" "$SCRIPT" "$REPORT" <<'PY'
import json
import sys
from pathlib import Path

root, label, output, staged, script, report = sys.argv[1:]
commands = [
    f"command script import {root}/tools/lldb_probes/create_stereo_color_public_reconstruction/stage_vector_probe.py",
    f"script stage_vector_probe.reset({json.dumps(label)}, {json.dumps(output)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x27b7a0",
    "breakpoint set --shlib libcp.dylib --address 0x27d5b0",
    "breakpoint set --shlib libcp.dylib --address 0x33f180",
    "breakpoint set --shlib libcp.dylib --address 0x33f3e8",
    "breakpoint set --shlib libcp.dylib --address 0x341b30",
    "breakpoint set --shlib libcp.dylib --address 0xf9ef0",
    "breakpoint set --shlib libcp.dylib --address 0xfb6a0",
    "breakpoint set --shlib libcp.dylib --address 0xfebf0",
    "breakpoint set --shlib libcp.dylib --address 0x100560",
    "breakpoint set --shlib libcp.dylib --address 0x100680",
    "breakpoint set --shlib libcp.dylib --address 0x1019a0",
    "breakpoint set --shlib libcp.dylib --address 0x103120",
    "breakpoint set --shlib libcp.dylib --address 0x1053b0",
    "breakpoint set --shlib libcp.dylib --address 0x1054d0",
    "breakpoint set --shlib libcp.dylib --address 0x106c80",
    "breakpoint set --shlib libcp.dylib --address 0x342d99",
    "breakpoint set --shlib libcp.dylib --address 0x342b80",
    "breakpoint set --shlib libcp.dylib --address 0x2eb560",
    "script stage_vector_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(staged) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    f"script stage_vector_probe.write_report(lldb.debugger, {json.dumps(report)})",
    "script stage_vector_probe.assert_complete()",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

LLDB_ARGS=(-b)
while IFS= read -r command; do
  LLDB_ARGS+=(-o "$command")
done < "$SCRIPT"
exec arch -x86_64 lldb "${LLDB_ARGS[@]}"
