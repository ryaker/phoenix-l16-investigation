#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 STAGED_SINGLE_CAMERA_LRI RUN_LABEL CAMERA_KEY" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_guidance_channel_origin/collapse_input_sample_probe.py"
LRI="$1"
LABEL="$2"
CAMERA_KEY="$3"
OUT="$ROOT/runs/index5_guidance_channel_origin/collapse_input_$LABEL"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"
REPORT="$OUT/report.json"

mkdir -p "$OUT"
rm -f "$REPORT"
python3 - "$PROBE" "$LRI" "$LABEL" "$CAMERA_KEY" "$REPORT" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, lri, label, camera_key, report, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    "script collapse_input_sample_probe.reset(" +
    f"{json.dumps(label)}, {int(camera_key)}, {json.dumps(lri)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x3f5035",
    "breakpoint set --shlib libcp.dylib --address 0x27b7a0",
    "breakpoint set --shlib libcp.dylib --address 0x27d5b0",
    "breakpoint set --shlib libcp.dylib --address 0xa4ced",
    "breakpoint set --shlib libcp.dylib --address 0xa52fd",
    "breakpoint set --shlib libcp.dylib --address 0xa590d",
    "breakpoint set --shlib libcp.dylib --address 0xa5f1d",
    "script collapse_input_sample_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(report).with_suffix('.hdr'))) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script collapse_input_sample_probe.write_report(lldb.debugger, " +
    json.dumps(report) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$SCRIPT" > "$LOG" 2>&1
test -s "$REPORT"
python3 - "$REPORT" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["entry"] and report["packet"], "missing collapse sample"
assert len(report["packets"]) >= report["packet_limit"], "short packet capture"
assert report["terminated_after_capture"], "capture did not terminate"
print("collapse_input_sample=OK", report["packet"]["site"], len(report["packets"]))
print("lanes", report["packet"]["lanes_rg1g2b"])
PY
