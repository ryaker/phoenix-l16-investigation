#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 LRI RUN_LABEL COMMA_SEPARATED_CAMERA_KEYS" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_guidance_channel_origin/create_stereo_exposure_scale_probe.py"
LRI="$1"
LABEL="$2"
KEYS="$3"
OUT="$ROOT/runs/index5_guidance_channel_origin/create_stereo_exposure_$LABEL"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json" "$OUT"/key_*_pre.bin "$OUT"/key_*_post.bin
python3 - "$PROBE" "$OUT" "$LRI" "$KEYS" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, keys, script = sys.argv[1:]
expected = [int(value) for value in keys.split(",")]
commands = [
    f"command script import {probe}",
    "script create_stereo_exposure_scale_probe.reset(" +
    f"{json.dumps(Path(output).name)}, {json.dumps(output)}, {json.dumps(lri)}, {expected!r})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x27d803",
    "breakpoint set --shlib libcp.dylib --address 0x27d808",
    "breakpoint set --shlib libcp.dylib --address 0x27db43",
    "breakpoint set --shlib libcp.dylib --address 0x27db48",
    "breakpoint set --shlib libcp.dylib --address 0xe6a89",
    "script create_stereo_exposure_scale_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script create_stereo_exposure_scale_probe.write_report(lldb.debugger, " +
    json.dumps(str(Path(output) / "report.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["terminated_after_capture"], "capture did not terminate"
assert sorted(map(int, report["packets"])) == report["expected_keys"], report["packets"].keys()
print(
    "create_stereo_exposure_scale=OK",
    report["expected_keys"],
    [report["packets"][str(key)]["scalar"] for key in report["expected_keys"]],
)
PY
