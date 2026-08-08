#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
exec arch -x86_64 lldb -b \
  -s "$ROOT/tools/lldb_probes/prefusion_monofusion_mode1/unit1_35mm_profile1_invalid.lldb"
