#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/reference_stage_maps/unit1_28mm"
mkdir -p "$OUT"
arch -x86_64 lldb -s "$ROOT/tools/lldb_probes/reference_stage_maps/unit1_28mm.lldb" \
  > "$OUT/run.log" 2>&1
test -s "$OUT/report.json"
python3 - "$OUT/report.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert not d["errors"], d["errors"]
assert len(d["captures"]) == 4, len(d["captures"])
assert d["process"]["exit_status"] == 0, d["process"]
print("reference_stage_maps_28mm=OK", [(x["name"], x["sha256"]) for x in d["captures"]])
PY
