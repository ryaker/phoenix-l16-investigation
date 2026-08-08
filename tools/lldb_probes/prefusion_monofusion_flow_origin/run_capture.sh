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
SCRIPT="$OUT/capture.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$OUT/report.json"
python3 - "$PROBE" "$OUT" "$LRI" "$LABEL" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

probe, output, lri, label, script = sys.argv[1:]
commands = [
    f"command script import {probe}",
    f"script monofusion_flow_origin_probe.reset({json.dumps(label)})",
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --shlib libcp.dylib --address 0x1b25ed",
    "breakpoint set --shlib libcp.dylib --address 0x1b25f2",
    "breakpoint set --shlib libcp.dylib --address 0x1b25ff",
    "breakpoint set --shlib libcp.dylib --address 0x1b37a0",
    "breakpoint set --shlib libcp.dylib --address 0x1a477e",
    "breakpoint set --shlib libcp.dylib --address 0x1939b0",
    "breakpoint set --shlib libcp.dylib --address 0x1940a0",
    "breakpoint set --shlib libcp.dylib --address 0x1952e0",
    "breakpoint set --shlib libcp.dylib --address 0x196850",
    "breakpoint set --shlib libcp.dylib --address 0x1978f0",
    "breakpoint set --shlib libcp.dylib --address 0x198560",
    "script monofusion_flow_origin_probe.attach(lldb.debugger, "
    "{'producer_entry': 1, 'producer_return': 2, 'vector_copy': 3, "
    "'worker_entry': 4, 'flow_use': 5, "
    "'variant_1939b0': 6, 'variant_1940a0': 7, 'variant_1952e0': 8, "
    "'variant_196850': 9, 'variant_1978f0': 10, 'variant_198560': 11})",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "script monofusion_flow_origin_probe.write_report(" +
    json.dumps(str(Path(output) / "report.json")) + ")",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
test -s "$OUT/report.json"
python3 "$ROOT/tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_origin.py" \
  "$OUT/report.json"
