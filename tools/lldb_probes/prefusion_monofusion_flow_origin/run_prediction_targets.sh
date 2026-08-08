#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "usage: $0 LRI LABEL CALLER_RETURN_VA X,Y [X,Y ...]" >&2
  exit 2
fi

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_flow_origin_probe.py"
LRI="$1"
LABEL="$2"
CALLER_VA="$3"
shift 3
OUT="$ROOT/runs/prefusion_monofusion_flow_origin/$LABEL"
SCRIPT="$OUT/prediction_targets.lldb"
LOG="$OUT/prediction_targets.log"

mkdir -p "$OUT"
rm -f "$OUT/prediction_targets.json"
python3 - "$PROBE" "$OUT" "$LRI" "$LABEL" "$SCRIPT" "$CALLER_VA" "$@" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, label, script, caller, *raw_targets = sys.argv[1:]
targets = [[int(part) for part in item.split(",")] for item in raw_targets]
commands = [
    f"command script import {probe}",
    f"script monofusion_flow_origin_probe.reset({json.dumps(label)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x1962f0",
    "breakpoint set --shlib libcp.dylib --address 0x196781",
    "breakpoint set --shlib libcp.dylib --address 0x1991e0",
    "script monofusion_flow_origin_probe.attach_prediction(lldb.debugger, 1, 2, 3)",
    "script monofusion_flow_origin_probe.configure_prediction_targets(" +
    f"{int(caller, 0)}, {targets!r})",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script monofusion_flow_origin_probe.write_report(" +
    json.dumps(str(Path(output) / "prediction_targets.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/prediction_targets.json"
python3 - "$OUT/prediction_targets.json" "$#" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1]))
assert not report["errors"], report["errors"]
assert report["terminated_after_samples"]
for entry, result in zip(report["prediction_entries"], report["prediction_returns"]):
    print(
        "target",
        entry["grid"],
        "scale",
        entry["scale_r8"],
        "source",
        entry["source"]["size"],
        "previous",
        entry["previous_flow"]["size"],
        "=>",
        result["output"],
    )
PY
