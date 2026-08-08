#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/prefusion_owner_range_watch"
LOG="$OUT/owner_range_watch_28mm.log"
mkdir -p "$OUT"
rm -f "$OUT/owner_range_watch_28mm.json" "$OUT/owner_range_watch_28mm.hdr"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/prefusion_node_dest_sentinel_custody/owner_range_watch_28mm.lldb" \
  "$ROOT/tools/lri_process" > "$LOG" 2>&1 &
lldb_pid=$!

while kill -0 "$lldb_pid" 2>/dev/null; do
  if [[ -s "$LOG" ]] && rg -q 'lost connection' "$LOG"; then
    kill -TERM "$lldb_pid" 2>/dev/null || true
    wait "$lldb_pid" 2>/dev/null || true
    echo "owner-range probe rejected: LLDB lost debugserver connection" >&2
    exit 1
  fi
  sleep 1
done

set +e
wait "$lldb_pid"
status=$?
set -e

if rg -q 'lost connection' "$LOG"; then
  echo "owner-range probe rejected: LLDB lost debugserver connection" >&2
  exit 1
fi

exit "$status"
