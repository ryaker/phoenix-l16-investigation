#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
LRI="${1:-/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri}"
OUT="$ROOT/runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_guide_rows"
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/capture.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json"
cat > "$SCRIPT" <<EOF
command script import $ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_reference_operand_probe.py
script monofusion_reference_operand_probe.reset("Unit-1 exact-28mm A1 demosaic guide rows", "$OUT")
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
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
rows = report["demosaic_guide_rows"]
names = {"A0", "A1", "A2", "A3", "B0", "B1", "B2", "B3"}
assert all(set(item["rows"]) == names for item in rows)
assert all(
    value["halo_words"] == item["x1"] - item["x0"] + 16
    for item in rows for value in item["rows"].values()
)
targets = (0, 100, 1560, 3118)
segments = 0
for target_y in targets:
    intervals = sorted(
        (item["x0"], item["x1"])
        for item in rows
        if item["output_y"] == target_y
    )
    cursor = 0
    for begin, end in intervals:
        assert begin <= cursor, (target_y, cursor, intervals)
        cursor = max(cursor, end)
    assert cursor == 4160, (target_y, cursor, intervals)
    segments += len(intervals)
print(f"a1_demosaic_guide_rows=OK pairs=4 segments={segments} "
      f"core_words={8 * 4 * 4160} halo_words={8 * (4 * 4160 + segments * 16)}")
PY
