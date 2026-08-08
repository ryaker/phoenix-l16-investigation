#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 LRI RUN_LABEL" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/reference_stage_maps/reference_stage_map_probe.py"
LRI="$1"
LABEL="$2"
OUT="$ROOT/runs/reference_stage_maps/$LABEL"
LOG="$OUT/run.log"
LLDB_SCRIPT="$OUT/capture.lldb"

if [[ ! -f "$LRI" ]]; then
  echo "missing LRI: $LRI" >&2
  exit 2
fi

mkdir -p "$OUT"
python3 - "$PROBE" "$OUT" "$LRI" "$LLDB_SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, script = sys.argv[1:]
label = Path(output).name
commands = [
    f"command script import {probe}",
    "script reference_stage_map_probe.reset(" +
    f"{json.dumps(label + ' complete reference stage maps')}, " +
    f"{json.dumps(output)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "process handle SIGSEGV -p true -s false -n false",
    "breakpoint set --shlib libcp.dylib --address 0x26e4d5",
    "breakpoint set --shlib libcp.dylib --address 0x26e64f",
    "breakpoint set --shlib libcp.dylib --address 0x26ac18",
    "breakpoint set --shlib libcp.dylib --address 0x41eb5a",
    "script reference_stage_map_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.dng")) +
    " --profile 3 --export-fmt 4 --no-auto-lris",
    "script reference_stage_map_probe.write_report(lldb.debugger, " +
    json.dumps(str(Path(output) / "report.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$LLDB_SCRIPT" > "$LOG" 2>&1
test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert len(report["captures"]) == 4, len(report["captures"])
assert report["process"]["exit_status"] == 0, report["process"]
print("reference_stage_maps=OK", [(x["name"], x["sha256"]) for x in report["captures"]])
PY
