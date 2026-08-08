#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LRI LABEL OUTPUT_NAME" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_perlevel_projection_scale/perlevel_projection_probe.py"
LRI="$1"
LABEL="$2"
NAME="$3"
OUT="$ROOT/runs/index5_perlevel_projection_scale/$NAME"
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
    "script perlevel_projection_probe.reset(" +
    f"{json.dumps(label)}, {json.dumps(lri)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x276a01",
    "script perlevel_projection_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(report).with_suffix('.hdr'))) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script perlevel_projection_probe.write_report(lldb.debugger, " +
    json.dumps(report) + ")",
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
expected = [[65, 49], [130, 98], [260, 195], [520, 390], [1040, 780], [2080, 1560]]
packets = sorted(report["packets"], key=lambda item: item["index"])
dims = [item["guidance"]["size"] for item in packets]
steps = [item["image_coordinate_step_0x1c"] for item in packets]
assert not report["errors"], report["errors"]
assert dims == expected, dims
assert steps == [32, 16, 8, 4, 2, 1], steps
assert report["terminated_after_capture"], "capture did not terminate"
reference_projection = [item["raw_hex"] for item in packets[0]["projection_records"]]
for packet in packets:
    assert packet["layer_dimensions_0x2b8"] == packet["guidance"]["size"]
    assert len(packet["images"]) == 5
    assert all(item["descriptor"]["size"] == [2080, 1560] for item in packet["images"])
    assert len(packet["projection_records"]) == 4
    assert all(item["scale"] == [1.0, 1.0] for item in packet["projection_records"])
    assert [item["raw_hex"] for item in packet["projection_records"]] == reference_projection
print("perlevel_projection=OK", report["label"])
for packet in packets:
    print(
        f"index={packet['index']}",
        f"guidance={packet['guidance']['size']}",
        f"image_step={packet['image_coordinate_step_0x1c']}",
        f"images={[item['descriptor']['size'] for item in packet['images']]}",
        f"scales={[item['scale'] for item in packet['projection_records']]}",
    )
PY
