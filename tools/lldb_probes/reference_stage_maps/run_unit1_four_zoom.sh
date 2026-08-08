#!/bin/bash
set -euo pipefail

ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
for focal in 28 35 70 150; do
  OUT="$ROOT/runs/reference_stage_maps/unit1_${focal}mm"
  mkdir -p "$OUT"
  arch -x86_64 lldb -s \
    "$ROOT/tools/lldb_probes/reference_stage_maps/unit1_${focal}mm.lldb" \
    > "$OUT/run.log" 2>&1
done

python3 - "$ROOT/runs/reference_stage_maps" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for focal in (28, 35, 70, 150):
    report = json.loads((root / f"unit1_{focal}mm/report.json").read_text())
    assert not report["errors"], (focal, report["errors"])
    assert report["process"]["exit_status"] == 0, (focal, report["process"])
    assert len(report["captures"]) == 4, (focal, len(report["captures"]))
    names = {item["name"] for item in report["captures"]}
    assert names == {
        "index5_hypothesis_index",
        "index5_depth",
        "upsampled_depth",
        "gdepth_full",
    }, (focal, names)
    for item in report["captures"]:
        path = pathlib.Path(item["path"])
        assert path.stat().st_size == item["logical_bytes"], (focal, item["name"])
    print(f"reference_stage_maps_{focal}mm=OK")
PY
