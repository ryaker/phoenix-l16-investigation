#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIR="$ROOT/tools/lldb_probes/index5_nondeterminism"

arch -x86_64 lldb -b -s "$DIR/parent_decision_unit2_70mm_r1.lldb"
arch -x86_64 lldb -b -s "$DIR/parent_decision_unit2_70mm_r2.lldb"

python3 "$DIR/summarize_parent_decision_repeat.py"
