#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 4 ]]; then
  echo "usage: $0 LRI RUN_LABEL [CAMERA_KEY] [SINGLE_CAMERA_0_OR_1]" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/index5_guidance_channel_origin/create_stereo_color_stage_probe.py"
LRI="$1"
LABEL="$2"
CAMERA_KEY="${3:-0}"
SINGLE_CAMERA="${4:-0}"
OUT="$ROOT/runs/index5_guidance_channel_origin/create_stereo_color_$LABEL"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json" "$OUT/pre_collapse.f32" "$OUT/post_collapse.rgba32f" "$OUT/post_softisp.rgba32f" "$OUT/pre_color.rgba32f" "$OUT/post_color.rgba32f" "$OUT/packed_u8.rgba8"
python3 - "$PROBE" "$OUT" "$LRI" "$CAMERA_KEY" "$SINGLE_CAMERA" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, camera_key, single_camera, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    "script create_stereo_color_stage_probe.reset(" +
    f"{json.dumps(Path(output).name)}, {json.dumps(output)}, {int(camera_key)}, " +
    f"{json.dumps(lri)}, {bool(int(single_camera))})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x3f5035",
    "breakpoint set --shlib libcp.dylib --address 0x27b7a0",
    "breakpoint set --shlib libcp.dylib --address 0xa4ac0",
    "breakpoint set --shlib libcp.dylib --address 0xa50d0",
    "breakpoint set --shlib libcp.dylib --address 0xa56e0",
    "breakpoint set --shlib libcp.dylib --address 0xa5cf0",
    "breakpoint set --shlib libcp.dylib --address 0xa4f55",
    "breakpoint set --shlib libcp.dylib --address 0xa5565",
    "breakpoint set --shlib libcp.dylib --address 0xa5b75",
    "breakpoint set --shlib libcp.dylib --address 0xa6185",
    "breakpoint set --shlib libcp.dylib --address 0x27bcd7",
    "breakpoint set --shlib libcp.dylib --address 0x27bcdc",
    "breakpoint set --shlib libcp.dylib --address 0x27bd07",
    "breakpoint set --shlib libcp.dylib --address 0x27bfdb",
    "breakpoint set --shlib libcp.dylib --address 0x27ae60",
    "breakpoint set --shlib libcp.dylib --address 0x27bff5",
    "breakpoint set --shlib libcp.dylib --address 0x27c93b",
    "script create_stereo_color_stage_probe.attach(lldb.debugger)",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script create_stereo_color_stage_probe.write_report(lldb.debugger, " +
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
assert report["pre_collapse"] and report["post_collapse"] and report["post_softisp"] and report["pre_color"] and report["post_color"] and report["packed_u8"], "missing color stage"
assert report["color_callback"], "missing color callback"
assert report["terminated_after_capture"], "capture did not terminate"
print(
    "create_stereo_color_stage=OK",
    report["entry"]["source_key"],
    report["pre_collapse"]["artifact"]["sha256"],
    report["post_collapse"]["artifact"]["sha256"],
    report["post_softisp"]["artifact"]["sha256"],
    report["pre_color"]["artifact"]["sha256"],
    report["post_color"]["artifact"]["sha256"],
)
print("matrix", report["pre_color"]["matrix_rows"])
print(
    "worker",
    hex(report["color_callback"]["worker"]),
    "va",
    hex(report["color_callback"]["worker_va"]),
)
PY
