#!/usr/bin/env bash
set -euo pipefail

cd /Volumes/Dev/L16_Lumen_ReverseEngineering

mkdir -p runs/state_helper_23faf0_record_chain

arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_28mm.lldb > runs/state_helper_23faf0_record_chain/record_chain_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_35mm.lldb > runs/state_helper_23faf0_record_chain/record_chain_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_70mm.lldb > runs/state_helper_23faf0_record_chain/record_chain_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_150mm.lldb > runs/state_helper_23faf0_record_chain/record_chain_150mm.log
