#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LRI LABEL OUTPUT_NAME" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_skip_consumption/skip_consumption_probe.py"
LRI="$1"
LABEL="$2"
NAME="$3"
OUT="$ROOT/runs/index5_skip_consumption/$NAME"
SCRIPT="$OUT/capture.lldb"
REPORT="$OUT/report.json"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$REPORT"
python3 - "$PROBE" "$LRI" "$LABEL" "$REPORT" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, lri, label, report, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    "script skip_consumption_probe.reset(" + f"{json.dumps(label)}, {json.dumps(lri)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x276860",
    "script skip_consumption_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(report).with_suffix('.hdr'))) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script skip_consumption_probe.resume_until_complete(lldb.debugger)",
    "script skip_consumption_probe.write_report(lldb.debugger, " + json.dumps(report) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$REPORT"
python3 - "$REPORT" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["capture_complete"], "capture incomplete"
computed = report["pixels"]["computed"]
skipped = report["pixels"]["skipped"]
assert computed["mask"] == 0
assert skipped["mask"] != 0
assert any(computed["local_ready"]), computed["local_ready"]
assert not any(skipped["local_ready"]), skipped["local_ready"]
print("index5_skip_consumption=OK", report["label"])
for pixel in (computed, skipped):
    print(
        pixel["polarity"],
        "xy", (pixel["x"], pixel["y"]),
        "mask", pixel["mask"],
        "local", pixel["local_ready"][:8],
    )
PY
