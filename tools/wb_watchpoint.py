#!/usr/bin/env python3
"""
LLDB Python script to find WB gain write site.
Usage: lldb -s wb_watchpoint.py lri_process -- /path/to.lri /tmp/out.tiff
"""
import lldb
import sys

# This script uses LLDB's Python API
# Run as: python3 wb_watchpoint.py
# Or within LLDB: command script import wb_watchpoint.py

def find_wb_write_site(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()

    # Address of LinearizeAndColorScale setup function
    LINEARIZE_ADDR = 0x352ce0

    # Get the base address of libcp.dylib
    for module in target.module_iter():
        if 'libcp' in str(module.GetFileSpec()):
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            print(f"libcp base: 0x{base:x}")
            break

    print(f"LinearizeAndColorScale at: 0x{LINEARIZE_ADDR:x}")
    print("Use 'br set -a 0x352ce0+<libcp_base>' manually if needed")

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f wb_watchpoint.find_wb_write_site find_wb_write')
    print("wb_watchpoint module loaded. Use 'find_wb_write' command.")
