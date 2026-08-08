#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/runs/rcpss_emulation"
mkdir -p "$OUT"

clang -arch x86_64 -O2 \
  "$ROOT/tools/validation/dump_x86_rcpss.c" \
  -o "$OUT/dump_x86_rcpss"
codesign --force --sign - "$OUT/dump_x86_rcpss"
arch -x86_64 "$OUT/dump_x86_rcpss" selftest
