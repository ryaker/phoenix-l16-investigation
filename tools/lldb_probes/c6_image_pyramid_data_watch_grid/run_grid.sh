#!/usr/bin/env zsh
set -u

ROOT="${ROOT:-/Users/ryaker/Dev/L16_Lumen_ReverseEngineering}"
OUT_DIR="$ROOT/runs/c6_image_pyramid_data_watch_grid"
SCRIPT_DIR="$OUT_DIR/scripts"
RUN_ID="${RUN_ID:-$(date +%Y%m%dT%H%M%S)}"
STATUS_DIR="$OUT_DIR/status/$RUN_ID"
MAX_JOBS="${MAX_JOBS:-1}"
ZOOMS_FILTER="${1:-${ZOOMS:-70mm 150mm}}"
LEVELS_FILTER="${2:-${LEVELS:-0 1 2 3 4}}"
RANGES_FILTER="${3:-${RANGES:-first middle last}}"
PROBE="$ROOT/tools/lldb_probes/c6_image_pyramid_data_watch_grid/c6_image_pyramid_data_watch_grid_probe.py"
LRI_PROCESS="$ROOT/tools/lri_process"
LUMEN_FRAMEWORKS="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"

mkdir -p "$SCRIPT_DIR" "$STATUS_DIR"

write_lldb_script() {
  local name="$1"
  local label="$2"
  local lri="$3"
  local level="$4"
  local range_kind="$5"
  local lldb_script="$SCRIPT_DIR/$name.lldb"
  local json="$OUT_DIR/$name.json"
  local hdr="$OUT_DIR/$name.hdr"
  if (( MAX_JOBS == 1 )); then
    hdr="$OUT_DIR/c6_image_pyramid_data_watch_grid_render_sink.hdr"
  fi

  cat > "$lldb_script" <<LLDB
command script import $PROBE
script c6_image_pyramid_data_watch_grid_probe.reset("$label", $level, "$range_kind", 8, 32, 24000)
settings set target.env-vars DYLD_FRAMEWORK_PATH=$LUMEN_FRAMEWORKS DYLD_LIBRARY_PATH=$LUMEN_FRAMEWORKS
platform shell mkdir -p $OUT_DIR
target create $LRI_PROCESS
script c6_image_pyramid_data_watch_grid_probe.install_breakpoint(lldb.debugger)
process launch -- "$lri" "$hdr" --profile 3 --export-fmt 3 --no-auto-lris
script c6_image_pyramid_data_watch_grid_probe.drive_until_exit_or_step_cap(lldb.debugger)
script c6_image_pyramid_data_watch_grid_probe.report_to_file(lldb.debugger, "$json")
quit
LLDB
}

run_one() {
  local zoom="$1"
  local lri="$2"
  local level="$3"
  local range_kind="$4"
  local name="c6_image_pyramid_data_watch_grid_${zoom}_l${level}_${range_kind}"
  local label="${zoom} C6 ImagePyramid data watch grid level ${level} ${range_kind}"
  local lldb_script="$SCRIPT_DIR/$name.lldb"
  local log="$OUT_DIR/$name.log"
  local json="$OUT_DIR/$name.json"
  local status_file="$STATUS_DIR/$name.status"

  write_lldb_script "$name" "$label" "$lri" "$level" "$range_kind"
  arch -x86_64 lldb -b -s "$lldb_script" > "$log" 2>&1
  local exit_code="$?"
  if [[ "$exit_code" == "0" ]]; then
    python3 -c 'import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path, "r", encoding="utf-8"))
except Exception:
    sys.exit(1)
counts = data.get("counts") or {}
ok = (
    data.get("process_exit_status") == 0
    and not data.get("drive_hit_step_cap")
    and len(data.get("errors") or []) == 0
    and counts.get("watchpoints_armed") == 1
)
sys.exit(0 if ok else 1)' "$json"
    if [[ "$?" != "0" ]]; then
      exit_code=2
    fi
  fi
  print -r -- "$exit_code" > "$status_file"
  print -r -- "DONE ${name} status=${exit_code}"
  return "$exit_code"
}

job_count() {
  jobs -p | wc -l | tr -d ' '
}

throttle_jobs() {
  while (( $(job_count) >= MAX_JOBS )); do
    sleep 1
  done
}

launch_grid() {
  local zoom lri level range_kind

  print -r -- "RUN_ID=$RUN_ID MAX_JOBS=$MAX_JOBS ZOOMS=[$ZOOMS_FILTER] LEVELS=[$LEVELS_FILTER] RANGES=[$RANGES_FILTER]"

  for zoom in ${(z)ZOOMS_FILTER}; do
    if [[ "$zoom" == "70mm" ]]; then
      lri="/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
    elif [[ "$zoom" == "150mm" ]]; then
      lri="/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"
    else
      print -r -- "SKIP unknown zoom '$zoom'"
      continue
    fi

    for level in ${(z)LEVELS_FILTER}; do
      for range_kind in ${(z)RANGES_FILTER}; do
        print -r -- "START ${zoom} level=${level} range=${range_kind}"
        if (( MAX_JOBS <= 1 )); then
          run_one "$zoom" "$lri" "$level" "$range_kind"
        else
          run_one "$zoom" "$lri" "$level" "$range_kind" &
          throttle_jobs
        fi
      done
    done
  done

  if (( MAX_JOBS > 1 )); then
    wait || true
  fi
}

launch_grid

failed=0
for status_file in "$STATUS_DIR"/*.status(N); do
  [[ -e "$status_file" ]] || continue
  exit_code="$(<"$status_file")"
  if [[ "$exit_code" != "0" ]]; then
    print -r -- "FAILED $(basename "$status_file" .status) status=$exit_code"
    failed=1
  fi
done

exit "$failed"
