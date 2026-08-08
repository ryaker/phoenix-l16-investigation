#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
OUT="$ROOT/runs/reference_stage_maps/unit1_28mm_repeat"
mkdir -p "$OUT"
arch -x86_64 lldb -s \
  "$ROOT/tools/lldb_probes/reference_stage_maps/unit1_28mm_repeat.lldb" \
  > "$OUT/run.log" 2>&1
python3 - "$OUT/report.json" <<'PY'
import json, pathlib, sys
d = json.load(open(sys.argv[1]))
assert not d["errors"], d["errors"]
assert d["process"]["exit_status"] == 0, d["process"]
assert len(d["captures"]) == 4, len(d["captures"])
for item in d["captures"]:
    assert pathlib.Path(item["path"]).stat().st_size == item["logical_bytes"]
print("reference_stage_maps_28mm_repeat=OK")
PY
