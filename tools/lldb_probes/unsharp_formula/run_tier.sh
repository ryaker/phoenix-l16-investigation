#!/bin/sh
set -eu
if [ "$#" -ne 3 ]; then
  echo "usage: $0 LABEL SOURCE_LRI OUTPUT_STEM" >&2
  exit 2
fi
ROOT=/Volumes/Dev/L16_Lumen_ReverseEngineering
LABEL=$1
SOURCE=$2
STEM=$3
RUN="$ROOT/runs/unsharp_formula"
STAGED="/Users/ryaker/${STEM}_unsharp_probe.lri"
OUTPUT="/Users/ryaker/${STEM}_unsharp_probe.hdr"
mkdir -p "$RUN"
cp "$SOURCE" "$STAGED"
trap 'rm -f "$STAGED" "$OUTPUT" "$LLDB_SCRIPT"' EXIT
LLDB_SCRIPT="/Users/ryaker/${STEM}_unsharp_probe.lldb"
sed -e "s|@LABEL@|$LABEL|g" -e "s|@INPUT@|$STAGED|g" -e "s|@OUTPUT@|$OUTPUT|g" -e "s|@REPORT@|$RUN/$STEM.json|g" \
  "$ROOT/tools/lldb_probes/unsharp_formula/template.lldb" > "$LLDB_SCRIPT"
arch -x86_64 lldb -s "$LLDB_SCRIPT" "$ROOT/tools/lri_process" > "$RUN/$STEM.log" 2>&1
if [ -f "$OUTPUT" ]; then mv "$OUTPUT" "$RUN/$STEM.hdr"; fi
