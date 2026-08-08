#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/calibstage_public_names"
UNIT1_SOURCE="/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri"
UNIT2_SOURCE="/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri"
UNIT1_SCRATCH="/private/tmp/l16_calibstage_unit1_35mm.lri"
UNIT2_SCRATCH="/private/tmp/l16_calibstage_unit2_35mm.lri"
UNIT1_SHA256="71eff3d02b8b85af7f3256895eee0fcca073bb745939534abfd7eac83533b0ba"
UNIT2_SHA256="018aa5af4e94830c495eedb039beb7d3fce8d010c5b034ab9ebe38b2c3eed664"
mkdir -p "$OUT"

stage_lri() {
  local source="$1"
  local scratch="$2"
  local expected="$3"
  cp "$source" "$scratch"
  local actual
  actual="$(shasum -a 256 "$scratch" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "staged LRI SHA-256 mismatch: $actual" >&2
    exit 1
  fi
}

stage_lri "$UNIT1_SOURCE" "$UNIT1_SCRATCH" "$UNIT1_SHA256"
stage_lri "$UNIT2_SOURCE" "$UNIT2_SCRATCH" "$UNIT2_SHA256"

arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/calibstage_public_names/unit1_35mm.lldb" \
  > "$OUT/unit1_35mm.log" 2>&1
cp /private/tmp/l16_calibstage_unit1_35mm.hdr "$OUT/unit1_35mm.hdr"
arch -x86_64 lldb -b -s \
  "$ROOT/tools/lldb_probes/calibstage_public_names/unit2_35mm.lldb" \
  > "$OUT/unit2_35mm.log" 2>&1
cp /private/tmp/l16_calibstage_unit2_35mm.hdr "$OUT/unit2_35mm.hdr"

python3 \
  "$ROOT/tools/lldb_probes/calibstage_public_names/verify_calibstage_public_names.py"
