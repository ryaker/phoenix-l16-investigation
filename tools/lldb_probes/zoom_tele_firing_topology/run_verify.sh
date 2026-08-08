#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
exec python3 "$ROOT/tools/lldb_probes/zoom_tele_firing_topology/verify_tele_firing_topology.py" \
  --json-out "$ROOT/runs/zoom_tele_firing_topology/report.json"
