#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 LRI LABEL" >&2
  exit 2
fi

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
PROBE="$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_flow_origin_probe.py"
LRI="$1"
LABEL="$2"
OUT="$ROOT/runs/prefusion_monofusion_flow_origin/$LABEL"
SCRIPT="$OUT/variant_operands.lldb"
LOG="$OUT/variant_operands.log"

mkdir -p "$OUT"
rm -f "$OUT/variant_operands.json"
python3 - "$PROBE" "$OUT" "$LRI" "$LABEL" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, label, script = sys.argv[1:]
variants = [0x1939B0, 0x1940A0, 0x1952E0, 0x196850, 0x1978F0, 0x198560]
commands = [
    f"command script import {probe}",
    f"script monofusion_flow_origin_probe.reset({json.dumps(label)})",
    f"script monofusion_flow_origin_probe.set_dump_dir({json.dumps(output)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x1b25ed",
]
for va in variants:
    commands.append(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
ids = {"producer_entry": 1}
ids.update({f"variant_{va:x}": index + 2 for index, va in enumerate(variants)})
commands.extend([
    "script monofusion_flow_origin_probe.attach_variant_operands(lldb.debugger, " + repr(ids) + ")",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script monofusion_flow_origin_probe.write_report(" +
    json.dumps(str(Path(output) / "variant_operands.json")) + ")",
    "quit",
])
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/variant_operands.json"
python3 - "$OUT/variant_operands.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1]))
assert not report["errors"], report["errors"]
assert report["terminated_after_samples"]
for item in report["variant_hits"]:
    print(
        item["variant"],
        "scale",
        item["scale_value"],
        "reference",
        item["operands"]["reference"].get("size"),
        "source",
        item["operands"]["source"].get("size"),
        "previous",
        item["operands"]["previous_flow"].get("size"),
        "output",
        item["operands"]["output"].get("size"),
    )
PY
