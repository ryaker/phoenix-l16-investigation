#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LRI LABEL OUTPUT_NAME" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_sgm_cost_input/sgm_cost_input_probe.py"
LRI="$1"
LABEL="$2"
NAME="$3"
OUT="$ROOT/runs/index5_sgm_cost_input/$NAME"
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
    "script sgm_cost_input_probe.reset(" + f"{json.dumps(label)}, {json.dumps(lri)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x2773e1",
    "breakpoint set --shlib libcp.dylib --address 0x277567",
    "breakpoint set --shlib libcp.dylib --address 0x2779b0",
    "script sgm_cost_input_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(report).with_suffix('.hdr'))) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script sgm_cost_input_probe.write_report(lldb.debugger, " + json.dumps(report) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$REPORT"
python3 - "$REPORT" <<'PY'
import json
import math
import struct
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["capture_complete"], "capture incomplete"
events = {event["site"]: event for event in report["events"]}
raw = events["after_g42"]
normalized = events["after_normalize"]
sgm = events["sgm_recurrence"]
assert raw["projection_count"] == 4, raw["projection_count"]
assert math.isclose(raw["factor"], (1.0 / 27.0) / 4.0, rel_tol=0.0, abs_tol=1e-9)
def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]

expected = [int(f32(value * raw["factor"])) for value in raw["cost_u16"]]
assert normalized["cost_u16"] == expected, (raw["cost_u16"], normalized["cost_u16"], expected)
assert sgm["r10_is_temp"]
assert sgm["local_cost_lanes"] == normalized["cost_u16"][sgm["rdx"] : sgm["rdx"] + 8]
print("index5_sgm_cost_input=OK", report["label"])
print("projection_count", raw["projection_count"], "factor", raw["factor"])
print("raw", raw["cost_u16"][:16])
print("normalized", normalized["cost_u16"][:16])
print("sgm_lanes", sgm["local_cost_lanes"])
PY
