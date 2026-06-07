#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/ryaker/Dev/L16_Lumen_ReverseEngineering"
arch -x86_64 lldb -b -s "$ROOT/tools/lldb_probes/codex_source_record_payload_watch/payload_watch_28mm.lldb"
