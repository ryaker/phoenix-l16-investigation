#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LRI LABEL OUTPUT_NAME" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_range_pool_policy/range_pool_probe.py"
LRI="$1"
LABEL="$2"
NAME="$3"
OUT="$ROOT/runs/index5_range_pool_policy/$NAME"
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
    "script range_pool_probe.reset(" +
    f"{json.dumps(label)}, {json.dumps(lri)}, {json.dumps(str(Path(report).parent))})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x26d8ac",
    "script range_pool_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(report).with_suffix('.hdr'))) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script range_pool_probe.write_report(lldb.debugger, " + json.dumps(report) + ")",
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
assert report["terminated_after_capture"], "capture did not terminate"
packets = sorted(report["packets"], key=lambda packet: packet["target_dimensions"])
assert len(packets) == 5, len(packets)
assert [packet["kernel_size_0x14"] for packet in packets] == [4] * 5
for packet in packets:
    for sample in packet["samples"]:
        assert sample["observed_low"] == sample["expected_low"], sample
        assert sample["observed_high"] == sample["expected_high"], sample
print("index5_range_pool=OK", report["label"])
for packet in packets:
    print(
        f"target={packet['target_dimensions']}",
        f"source={[packet['source']['width'], packet['source']['height']]}",
        f"kernel={packet['kernel_size_0x14']}",
        f"samples={[(sample['kind'], sample['observed_low'], sample['observed_high']) for sample in packet['samples']]}",
    )
PY
