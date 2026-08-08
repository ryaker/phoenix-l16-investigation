#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="${HOTPIXEL_OUT:-$ROOT/runs/prefusion_monofusion_flow_origin/unit1_28mm_hotpixel_preprocess}"
LABEL="${HOTPIXEL_LABEL:-Unit-1 exact-28mm A2 MonoFusion hot-pixel preprocessing}"
LRI="${HOTPIXEL_LRI:-/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri}"
SCRIPT="$OUT/probe.lldb"
LOG="$OUT/probe.log"
mkdir -p "$OUT"
rm -f "$OUT/report.json"

cat >"$SCRIPT" <<LLDB
command script import $ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_hotpixel_preprocess_probe.py
script monofusion_hotpixel_preprocess_probe.reset("$LABEL", "$OUT", False)
settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
breakpoint set --shlib libcp.dylib --address 0x2e8680
breakpoint set --shlib libcp.dylib --address 0x2e87d6
breakpoint set --shlib libcp.dylib --address 0x2e8cc0
breakpoint set --shlib libcp.dylib --address 0x2e8d07
breakpoint set --shlib libcp.dylib --address 0x10acd0
script monofusion_hotpixel_preprocess_probe.attach(lldb.debugger)
process launch -- "$LRI" "$OUT/output.hdr" --profile 3 --export-fmt 3 --no-auto-lris
script monofusion_hotpixel_preprocess_probe.drive(lldb.debugger)
script monofusion_hotpixel_preprocess_probe.write_report(lldb.debugger, "$OUT/report.json")
quit
LLDB

arch -x86_64 lldb -b -s "$SCRIPT" \
  /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process >"$LOG" 2>&1

test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert report["complete"], report
assert report["worker"], report
assert all(item["bytes"] == 4096 for item in report["worker"]["luts"]), report["worker"]["luts"]
assert len(report["clipped_views"]) == 4, report["clipped_views"]
assert not report["target_decisions"], report["target_decisions"]
assert not report["errors"], report["errors"]
print(
    "monofusion_hotpixel_preprocess_capture=OK",
    "phase=" + repr(report["worker"]["phase"]),
    "threshold=" + repr(report["worker"]["threshold_multiplier"]),
    "lut_sha=" + repr([item["sha256"] for item in report["worker"]["luts"]]),
    "worker_count=" + str(len(report["worker_entries"])),
    "clipped_views=" + repr(report["clipped_views"]),
    "rectangles=" + repr([item["rectangle"] for item in report["worker_entries"]]),
    "leakage_entries=" + str(len(report["leakage_entries"])),
    "target_decisions=" + repr(report["target_decisions"]),
    "input_sha=" + report["helper"]["source_dump"]["sha256"],
    "output_sha=" + report["helper"]["destination_dump"]["sha256"],
)
PY
