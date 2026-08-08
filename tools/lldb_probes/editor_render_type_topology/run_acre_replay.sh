#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/replay_acre_worker.c"
OUT="$ROOT/runs/editor_render_type_topology/replay_acre_worker"
INPUT="$ROOT/runs/editor_render_type_topology/stage_images/display_stage_14_349e80.raw"
LUT="$ROOT/runs/editor_render_type_topology/acre_lut_1025_f32.raw"
REPLAY="$ROOT/runs/editor_render_type_topology/acre_intermediate_replay_256x256_f32.raw"
EXPECTED="$ROOT/runs/editor_render_type_topology/acre_intermediate_first_256x256_f32.raw"

clang -arch x86_64 -O2 -msse4.1 -ffp-contract=off -Wall -Wextra \
    "$SRC" -o "$OUT"
arch -x86_64 "$OUT" "$INPUT" "$LUT" "$REPLAY"
shasum -a 256 "$EXPECTED" "$REPLAY"
cmp "$EXPECTED" "$REPLAY"
