#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 LRI RUN_LABEL" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_guidance_neutral_origin/neutral_route_probe.py"
LRI="$1"
LABEL="$2"
OUT="$ROOT/runs/index5_guidance_neutral_origin/$LABEL"
SCRIPT="$OUT/solver_trace.lldb"
REPORT="$OUT/report.json"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$REPORT" "$LOG" "$OUT/output.hdr"
python3 - "$PROBE" "$LRI" "$OUT" "$SCRIPT" <<'PY'
import json
import os
import sys
from pathlib import Path

probe, lri, output, script = sys.argv[1:]
sites = [
    0x2D36BA, 0x2D39D7, 0x2D3CC8, 0x2D3F54,
    0x2D3F86, 0x2D3FA0, 0x2D3FA5, 0x2D3FD9, 0x2D4004,
    0x2D424D, 0x2D4276,
]
if os.environ.get("L16_SOLVER_SITES"):
    sites = [int(value, 0) for value in os.environ["L16_SOLVER_SITES"].split(",")]
commands = [
    "settings set interpreter.stop-command-source-on-error false",
    "command script import " + probe,
    "script neutral_route_probe.reset(" +
    json.dumps(str(Path(output) / "report.json")) + ", " + json.dumps(lri) + ")",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
]
commands.extend(
    "breakpoint set --shlib libcp.dylib --address " + hex(site) for site in sites
)
commands.extend([
    "script neutral_route_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script neutral_route_probe.write_report(lldb.debugger)",
    "quit",
])
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$SCRIPT" > "$LOG" 2>&1
test -s "$REPORT"
python3 - "$REPORT" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["solver_traces"], "no completed solver traces"
print("guidance_neutral_solver_trace=OK", len(report["solver_traces"]))
for trace in report["solver_traces"]:
    print(
        "thread", trace["thread_id"],
        "points", trace["solver_points_ready"]["points"]["count"],
        "neutral", trace["solver_neutral_ready"]["neutral"]["f32"],
        "xy", trace["solver_xy_ready"]["xy"]["f32"],
    )
PY
