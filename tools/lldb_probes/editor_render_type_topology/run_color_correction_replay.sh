#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SRC="$ROOT/tools/lldb_probes/editor_render_type_topology/replay_color_correction.c"
OUT="$ROOT/runs/editor_render_type_topology/replay_color_correction"
INPUT="$ROOT/runs/editor_render_type_topology/stage_images/display_stage_03_340f70.raw"
MAP="$ROOT/runs/editor_render_type_topology/color_correction_hsv_map_vec4_f32.raw"
EXPECTED="$ROOT/runs/editor_render_type_topology/stage_images/display_stage_10_347680.raw"

clang -O2 -Wall -Wextra -ffp-contract=off "$SRC" -o "$OUT"
"$OUT" "$INPUT" "$MAP" "$EXPECTED"
