#!/bin/bash
# Exhaustive verification of the RSQRTSS/RSQRTPS seed emulation shipped in
# phoenix/engine/common/x86_rsqrt.h.  Sibling of verify_x86_rcp_emulation.sh.
#
# Runs the full 2^32-input sweep, so it needs an x86_64 execution environment.
# On an Apple Silicon Mac that means Rosetta; on an x86_64 Linux host it runs
# natively.  Expect roughly a minute.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/runs/rsqrt_emulation"
mkdir -p "$OUT"

if [ "$(uname -m)" = "x86_64" ]; then
  cc -O2 "$ROOT/tools/validation/dump_x86_rsqrtss.c" -o "$OUT/dump_x86_rsqrtss" -lm
  "$OUT/dump_x86_rsqrtss" structure
  "$OUT/dump_x86_rsqrtss" selftest
else
  clang -arch x86_64 -O2 "$ROOT/tools/validation/dump_x86_rsqrtss.c" \
    -o "$OUT/dump_x86_rsqrtss" -lm
  codesign --force --sign - "$OUT/dump_x86_rsqrtss"
  arch -x86_64 "$OUT/dump_x86_rsqrtss" structure
  arch -x86_64 "$OUT/dump_x86_rsqrtss" selftest
fi
