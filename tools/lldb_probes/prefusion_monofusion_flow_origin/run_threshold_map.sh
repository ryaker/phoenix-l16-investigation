#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 LRI LABEL" >&2
  exit 2
fi

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_flow_origin_probe.py"
LRI="$1"
LABEL="$2"
OUT="$ROOT/runs/prefusion_monofusion_flow_origin/$LABEL"
SCRIPT="$OUT/threshold_map.lldb"
LOG="$OUT/threshold_map.log"

mkdir -p "$OUT"
rm -f "$OUT/threshold_map.json"
python3 - "$PROBE" "$OUT" "$LRI" "$LABEL" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, label, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    f"script monofusion_flow_origin_probe.reset({json.dumps(label)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x1b1c1a",
    "script monofusion_flow_origin_probe.attach_threshold_map_build(lldb.debugger, 1)",
    "breakpoint set --shlib libcp.dylib --address 0x1b37a0",
    "script monofusion_flow_origin_probe.attach_threshold_map(lldb.debugger, 2)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script monofusion_flow_origin_probe.write_report(" +
    json.dumps(str(Path(output) / "threshold_map.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/threshold_map.json"
python3 - "$OUT/threshold_map.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1]))
assert not report["errors"], report["errors"]
assert len(report["threshold_map_builds"]) == 1
assert len(report["threshold_map_entries"]) == 1
entry = report["threshold_map_entries"][0]
values = [item["value"] for item in entry["samples"]["samples"]]
assert all(value is not None and value >= 1.0 for value in values), values
assert report["terminated_after_samples"]
print("threshold_map=CAPTURED", entry["descriptor"]["size"], entry["flow_threshold_0x200"], values)
PY
