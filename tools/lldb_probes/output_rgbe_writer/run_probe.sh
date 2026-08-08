#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
mkdir -p "$ROOT/runs/output_rgbe_writer"
exec arch -x86_64 lldb -s \
  "$ROOT/tools/lldb_probes/output_rgbe_writer/unit1_28mm.lldb" \
  "$ROOT/tools/lri_process"
