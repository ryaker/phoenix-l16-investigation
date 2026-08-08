#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RUNS="$ROOT/runs/reference_validation/self_repeats"
COUNT=${1:-10}
mkdir -p "$RUNS"

render_set() {
  label=$1
  lri=$2
  output_dir="$RUNS/$label"
  mkdir -p "$output_dir"
  index=1
  while [ "$index" -le "$COUNT" ]; do
    output="$output_dir/repeat_$(printf '%02d' "$index").hdr"
    log="$output_dir/repeat_$(printf '%02d' "$index").log"
    if [ ! -s "$output" ]; then
      attempt=1
      while :; do
        rm -f "$output"
        if arch -x86_64 "$ROOT/tools/lri_process" "$lri" "$output" \
          >"$log.attempt_$attempt" 2>&1; then
          cp "$log.attempt_$attempt" "$log"
          break
        fi
        rm -f "$output"
        if [ "$attempt" -ge 3 ]; then
          echo "render failed after $attempt attempts: $label repeat $index" >&2
          return 1
        fi
        sleep 30
        attempt=$((attempt + 1))
      done
    fi
    shasum -a 256 "$output" >"$output.sha256"
    sleep 5
    index=$((index + 1))
  done
}

render_set unit1_28mm "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
render_set unit1_35mm "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
render_set unit1_70mm "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
render_set unit1_150mm "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri"

exec python3 "$ROOT/tools/validation/analyze_self_repeats.py" \
  "$RUNS" \
  --json-out "$RUNS/analysis.json"
