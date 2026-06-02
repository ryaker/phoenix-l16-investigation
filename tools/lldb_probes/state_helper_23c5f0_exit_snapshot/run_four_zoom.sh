#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_helper_23c5f0_exit_snapshot

arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_28mm.lldb > runs/state_helper_23c5f0_exit_snapshot/snapshot_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_35mm.lldb > runs/state_helper_23c5f0_exit_snapshot/snapshot_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_70mm.lldb > runs/state_helper_23c5f0_exit_snapshot/snapshot_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_150mm.lldb > runs/state_helper_23c5f0_exit_snapshot/snapshot_150mm.log
