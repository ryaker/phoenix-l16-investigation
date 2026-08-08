#!/bin/bash
set -euo pipefail

ROOT=/Users/ryaker/Dev/L16_Lumen_ReverseEngineering
LLDB_DIR="$ROOT/tools/lldb_probes/new_lri_variant_census"

arch -x86_64 lldb -b -s "$LLDB_DIR/pipeline_64mm.lldb"
arch -x86_64 lldb -b -s "$LLDB_DIR/pipeline_71mm.lldb"
arch -x86_64 lldb -b -s "$LLDB_DIR/hotpixel_old150.lldb"
