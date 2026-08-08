#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 LRI RUN_LABEL" >&2
  exit 2
fi

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
LRI="$1"
LABEL="$2"
OUT="$ROOT/runs/index5_guidance_neutral_origin/$LABEL"
SCRIPT="$OUT/table_headers.lldb"
LOG="$OUT/run.log"

mkdir -p "$OUT"
rm -f "$LOG" "$OUT/output.hdr"
python3 - "$LRI" "$OUT" "$SCRIPT" <<'PY'
import json
import sys
from pathlib import Path

lri, output, script = sys.argv[1:]
commands = [
    "settings set target.env-vars "
    "DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks "
    "DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks",
    "target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process",
    "breakpoint set --one-shot true --shlib libcp.dylib --address 0x3427b7",
    "breakpoint command add 1 "
    "-o 'memory read --format x --size 4 --count 10 `$pc - 0x3427b7 + 0x6708f0`' "
    "-o 'memory read --format x --size 4 --count 10 `$pc - 0x3427b7 + 0x6708c0`' "
    "-o 'continue'",
    "process launch -- " + json.dumps(lri) + " " +
    json.dumps(str(Path(output) / "output.hdr")) +
    " --profile 3 --export-fmt 3 --no-auto-lris",
    "quit",
]
Path(script).write_text("\n".join(commands) + "\n", encoding="ascii")
PY

arch -x86_64 lldb -s "$SCRIPT" > "$LOG" 2>&1
rg -n "0x[0-9a-f]+: 0x" "$LOG"
