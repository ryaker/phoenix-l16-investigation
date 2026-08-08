#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/reference_stage_maps"
for sample in 3 4 5 6 7 8 9 10; do
  for focal in 28 35 70 150; do
    OUT="$ROOT/runs/reference_stage_maps/unit1_${focal}mm_repeat$(printf '%02d' "$sample")"
    mkdir -p "$OUT"
    arch -x86_64 lldb -b "$ROOT/tools/lri_process" \
      -o "command script import $PROBE_DIR/reference_stage_map_probe.py" \
      -o "command script import $PROBE_DIR/repeat_campaign_driver.py" \
      -o "script repeat_campaign_driver.run(lldb.debugger, $focal, $sample)" \
      -o quit >"$OUT/run.log" 2>&1
    python3 - "$OUT/report.json" "$focal" "$sample" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert report["process"]["exit_status"] == 0, report["process"]
assert len(report["captures"]) == 4, len(report["captures"])
print("reference_stage_map_repeat=OK", sys.argv[2], sys.argv[3])
PY
  done
done
