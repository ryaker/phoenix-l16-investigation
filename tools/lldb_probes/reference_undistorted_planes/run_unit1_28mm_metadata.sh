#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/reference_undistorted_planes/unit1_28mm_metadata"
mkdir -p "$OUT"
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/reference_undistorted_planes/unit1_28mm_metadata.lldb" \
  "$ROOT/tools/lri_process" >"$OUT/session.log" 2>&1
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert report["hit_count"] > 0, report
assert not report["errors"], report["errors"]
shapes = sorted({
    (tuple(hit["destination"]["origin"]), tuple(hit["destination"]["size"]),
     hit["destination"]["stride"])
    for hit in report["hits"]
})
print("undistort_boundary_metadata=OK", report["hit_count"], shapes)
PY
