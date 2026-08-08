#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/state5_handle_identity_two_body"
mkdir -p "$OUT"

run_probe() {
  local stem="$1"
  local script="$ROOT/tools/lldb_probes/calib_state_operator_runtime/${stem}.lldb"
  local log="$OUT/${stem}.log"

  rm -f "$OUT/${stem}.json" "$OUT/${stem}.hdr"
  arch -x86_64 lldb -b -s "$script" "$ROOT/tools/lri_process" > "$log" 2>&1 &
  local lldb_pid=$!

  while kill -0 "$lldb_pid" 2>/dev/null; do
    if [[ -s "$log" ]] && rg -q 'lost connection' "$log"; then
      kill -TERM "$lldb_pid" 2>/dev/null || true
      wait "$lldb_pid" 2>/dev/null || true
      echo "$stem rejected: LLDB lost debugserver connection" >&2
      return 1
    fi
    sleep 1
  done

  set +e
  wait "$lldb_pid"
  local status=$?
  set -e
  if rg -q 'lost connection' "$log"; then
    echo "$stem rejected: LLDB lost debugserver connection" >&2
    return 1
  fi
  return "$status"
}

run_probe state5_handle_identity_unit1_35mm
run_probe state5_handle_identity_unit1_70mm
run_probe state5_handle_identity_unit1_150mm
