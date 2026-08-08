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
SCRIPT="$OUT/capture.lldb"
REPORT="$OUT/report.json"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$REPORT" "$LOG" "$OUT/output.hdr"
python3 - "$PROBE" "$LRI" "$OUT" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, lri, output, script = sys.argv[1:]
sites = [
    0xE5720, 0xE574D, 0xE5752, 0x144560,
    0x1BD270, 0x1BD597, 0x1BD5A5, 0x1BD5CA, 0x1BD675, 0x1BD6A8,
    0x1BD715, 0x318218, 0x33E430, 0x33E5F1, 0x33E5F3, 0x33E611,
    0x33E613,
    0x342730, 0x342752, 0x3427B7, 0x3427BC,
]
commands = [
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
from collections import Counter

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["completed"], "no completed constructors"
routes = Counter(item["route"] for item in report["completed"])
print("guidance_neutral_capture=OK", len(report["completed"]), dict(routes))
for item in report["completed"]:
    gains = item.get("gains_optional")
    mode = item.get("mode_optional")
    print(
        "camera", item["camera_index"],
        "route", item["route"],
        "gains_present", gains["present"] if gains else None,
        "gains", gains["value"] if gains else None,
        "mode_present", mode["present"] if mode else None,
        "mode", mode["value"] if mode else None,
        "neutral", item.get("neutral"),
    )
PY
