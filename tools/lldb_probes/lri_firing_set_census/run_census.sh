#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$ROOT/runs/lri_firing_set_census/corpus_firing_sets.json"

python3 "$ROOT/tools/lldb_probes/lri_firing_set_census/census_lri_firing_sets.py" \
  --json-out "$OUT" \
  --quiet

python3 - "$OUT" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
print(
    "LRI_FIRING_SET_CENSUS "
    f"status={data['status']} lris={data['lri_count']} "
    f"complete={data['complete_count']} incomplete={data['incomplete_count']} "
    f"exceptions={data['exception_count']} "
    f"exact_focal_exceptions={data['exact_focal_exception_count']}"
)
PY
