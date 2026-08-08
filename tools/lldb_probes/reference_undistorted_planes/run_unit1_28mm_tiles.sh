#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/reference_undistorted_planes/unit1_28mm_tiles"
mkdir -p "$OUT"
arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/reference_undistorted_planes/unit1_28mm_tiles.lldb" \
  "$ROOT/tools/lri_process" >"$OUT/session.log" 2>&1
python3 - "$OUT/report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert report["process"]["exit_status"] == 0, report["process"]
assert report["hit_count"] > 0, report
assert report["tiles"], report
assert not report["errors"], report["errors"]
print(
    "source_cache_undistorted_tiles=OK",
    report["hit_count"],
    len(report["cache_objects"]),
    len(report["tiles"]),
)
PY
