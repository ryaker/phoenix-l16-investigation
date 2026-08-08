#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/capturedimage_f2770_origin
mkdir -p runs/capturedimage_f2770_origin/inputs

source_lri="/Volumes/Base Photos/Light/2018-07-23/L16_02153.lri"
local_lri="runs/capturedimage_f2770_origin/inputs/L16_02153.lri"
expected_sha256="c5796b9e960687ac14afc83d5e387964a834e502a28a1d9d8329f330fbae3136"

if [[ ! -f "$local_lri" ]] || [[ "$(shasum -a 256 "$local_lri" | awk '{print $1}')" != "$expected_sha256" ]]; then
  cp "$source_lri" "$local_lri"
fi

actual_sha256="$(shasum -a 256 "$local_lri" | awk '{print $1}')"
if [[ "$actual_sha256" != "$expected_sha256" ]]; then
  echo "multiframe LRI SHA-256 mismatch: $actual_sha256" >&2
  exit 1
fi

arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_multiframe_28mm.lldb
