#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_448_payload_public_origin

arch -x86_64 lldb -b -s tools/lldb_probes/state_448_payload_public_origin/state_448_payload_28mm.lldb > runs/state_448_payload_public_origin/state_448_payload_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_payload_public_origin/state_448_payload_35mm.lldb > runs/state_448_payload_public_origin/state_448_payload_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_payload_public_origin/state_448_payload_70mm.lldb > runs/state_448_payload_public_origin/state_448_payload_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_448_payload_public_origin/state_448_payload_150mm.lldb > runs/state_448_payload_public_origin/state_448_payload_150mm.log
