#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
for run in 28mm_tiles_repeat 35mm_tiles 70mm_tiles 150mm_tiles; do
  OUT="$ROOT/runs/reference_undistorted_planes/unit1_${run}"
  mkdir -p "$OUT"
  arch -x86_64 lldb -b \
    -s "$ROOT/tools/lldb_probes/reference_undistorted_planes/unit1_${run}.lldb" \
    "$ROOT/tools/lri_process" >"$OUT/session.log" 2>&1
  python3 - "$OUT/report.json" "$run" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert report["process"]["exit_status"] == 0, report["process"]
assert report["hit_count"] > 0, report
assert report["tiles"], report
assert not report["errors"], report["errors"]
print(
    "source_cache_undistorted_tiles=OK",
    sys.argv[2],
    report["hit_count"],
    len(report["cache_objects"]),
    len(report["tiles"]),
)
PY
done
