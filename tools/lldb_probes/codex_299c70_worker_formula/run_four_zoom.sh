#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
OUT="$ROOT/runs/codex_299c70_worker_formula"
mkdir -p "$OUT"

arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_worker_formula/static_worker_formula.lldb" > "$OUT/static_worker_formula.log"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_28mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_35mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_70mm.lldb"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_150mm.lldb"
