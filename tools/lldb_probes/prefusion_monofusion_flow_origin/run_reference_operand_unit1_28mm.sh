#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
LABEL="${1:-Unit-1 exact-28mm MonoFusion A1 reference operand}"
LRI="${2:-/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri}"
RUN_NAME="${3:-unit1_28mm_reference_operand}"
OUT="$ROOT/runs/prefusion_monofusion_flow_origin/$RUN_NAME"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/capture.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json"
cat > "$SCRIPT" <<EOF
command script import $ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_reference_operand_probe.py
script monofusion_reference_operand_probe.reset("$LABEL", "$OUT")
settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
breakpoint set --shlib libcp.dylib --address 0x1b5f60
breakpoint set --shlib libcp.dylib --address 0x1b6328
breakpoint set --shlib libcp.dylib --address 0x1b5660
breakpoint set --shlib libcp.dylib --address 0x1b5cda
breakpoint set --shlib libcp.dylib --address 0x1991e0
breakpoint set --shlib libcp.dylib --address 0x2eb560
script monofusion_reference_operand_probe.attach(lldb.debugger)
process launch -- "$LRI" "$OUT/output.hdr" --profile 3 --export-fmt 3 --no-auto-lris
script monofusion_reference_operand_probe.write_report("$OUT/report.json")
quit
EOF

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert len(report["entries"]) == 1, len(report["entries"])
assert len(report["returns"]) == 1, len(report["returns"])
assert len(report["affine_entries"]) == 1, len(report["affine_entries"])
assert len(report["affine_returns"]) == 1, len(report["affine_returns"])
assert report["demosaic_entry"] is not None
assert report["final_reference"] is not None
assert report["entries"][0]["source"]["size"] == [4160, 3120]
assert report["returns"][0]["output"]["size"] == [4160, 3120]
assert report["final_reference"]["count"] == 5
for path in (
    report["entries"][0]["source_dump"],
    report["returns"][0]["output_dump"],
    report["affine_returns"][0]["output_dump"],
    report["final_reference"]["level0_dump"],
    report["demosaic_entry"]["source_dump"],
):
    assert path["read_ok"], path
print(
    "monofusion_reference_operand_capture=OK",
    "weights=" + repr(report["entries"][0]["weights"]),
    "scalar=" + repr(report["entries"][0]["scalar"]),
    "scale=" + repr(report["affine_entries"][0]["scale"]),
    "cap=" + repr(report["affine_entries"][0]["cap"]),
    "phase=" + repr(report["demosaic_entry"]["phase"]),
    "gains=" + repr(report["demosaic_entry"]["gains"]),
    "source_sha256=" + report["entries"][0]["source_dump"]["sha256"],
    "scalar_sha256=" + report["returns"][0]["output_dump"]["sha256"],
    "level0_sha256=" + report["final_reference"]["level0_dump"]["sha256"],
)
PY
