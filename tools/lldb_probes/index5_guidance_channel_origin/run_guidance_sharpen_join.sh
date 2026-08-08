#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 LRI RUN_LABEL [CAMERA_KEY]" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_guidance_channel_origin/guidance_sharpen_join_probe.py"
LRI="$1"
LABEL="$2"
CAMERA_KEY="${3:-0}"
OUT="$ROOT/runs/index5_guidance_channel_origin/guidance_sharpen_join_$LABEL"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json"
python3 - "$PROBE" "$OUT" "$LRI" "$CAMERA_KEY" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, camera_key, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    "script guidance_sharpen_join_probe.reset(" +
    f"{json.dumps(Path(output).name)}, {json.dumps(output)}, {int(camera_key)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x3f5035",
    "breakpoint set --shlib libcp.dylib --address 0x27b7a0",
    "breakpoint set --shlib libcp.dylib --address 0xa50d0",
    "breakpoint set --shlib libcp.dylib --address 0x3589c0",
    "breakpoint set --shlib libcp.dylib --address 0x358fce",
    "breakpoint set --shlib libcp.dylib --address 0x108080",
    "script guidance_sharpen_join_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script guidance_sharpen_join_probe.write_report(lldb.debugger, " +
    json.dumps(str(Path(output) / "report.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["entry"], "missing selected CreateStereoImage entry"
assert report["collapse"], "missing GRBG collapse worker"
assert report["sharpen"] and report["sharpen"]["return"], "missing sharpen entry/return"
assert report["lens_match"], "missing joined lens worker"
assert report["terminated_after_match"], "capture did not terminate after join"
print("guidance_sharpen_join=OK")
print("packet", report["sharpen"]["config_f32"])
print("saturation", report["sharpen"]["saturation_xmm0"])
print("vibrance", report["sharpen"]["vibrance_xmm1"])
print("matching_allocations", report["lens_match"]["matching_allocations"])
print("spacing", report["lens_match"]["spacing"])
print("global_offset", report["lens_match"]["global_offset"])
PY
