#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
PROBE_DIR="$ROOT/tools/lldb_probes/reference_stage_maps"
for sample in 3 4 5 6 7 8 9 10; do
  for focal in 28 35 70 150; do
    OUT="$ROOT/runs/reference_stage_maps/unit1_${focal}mm_repeat$(printf '%02d' "$sample")"
    if python3 - "$OUT/report.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
if not path.exists():
    raise SystemExit(1)
report = json.loads(path.read_text(encoding="ascii"))
names = {item["name"] for item in report.get("captures", [])}
good = not report.get("errors") and {
    "index5_hypothesis_index",
    "index5_depth",
}.issubset(names)
raise SystemExit(0 if good else 1)
PY
    then
      echo "reference_stage_map_repeat=EXISTS $focal $sample"
      continue
    fi
    mkdir -p "$OUT"
    arch -x86_64 lldb -b "$ROOT/tools/lri_process" \
      -o "command script import $PROBE_DIR/reference_stage_map_probe.py" \
      -o "command script import $PROBE_DIR/early_repeat_campaign_driver.py" \
      -o "script early_repeat_campaign_driver.run(lldb.debugger, $focal, $sample)" \
      -o quit >"$OUT/early_run.log" 2>&1
    python3 - "$OUT/report.json" "$focal" "$sample" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="ascii"))
assert not report["errors"], report["errors"]
assert {item["name"] for item in report["captures"]} == {
    "index5_hypothesis_index",
    "index5_depth",
}, report["captures"]
print("reference_stage_map_repeat=OK", sys.argv[2], sys.argv[3])
PY
  done
done
