#!/usr/bin/env python3
"""
Probe ImageConvertColorSpace::$_0 at libcp+0xbf4a0 on 70mm L16_03434.lri

Run with:
  arch -x86_64 python3 probe_ics_70mm.py
  (uses lldb Python bindings from Xcode)
"""

import sys
import os
import struct
import time

# Add LLDB Python bindings to path
LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)

import lldb

LRI_PATH = '/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri'
OUT_PATH  = '/tmp/test_70mm_ics_out.tiff'
LRI_PROCESS_PATH = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'
ICS_OFFSET = 0xbf4a0

hit_count  = 0
matrix_hits  = {}   # mat_ptr (int) -> hit_count
matrix_data  = {}   # mat_ptr (int) -> list[float] | None
error_count  = 0


def ics_callback(frame, bp_loc, extra_args, internal_dict):
    global hit_count, error_count

    hit_count += 1

    process = frame.GetThread().GetProcess()

    rdi_reg = frame.FindRegister('rdi')
    if not rdi_reg.IsValid():
        error_count += 1
        return False

    closure_ptr = rdi_reg.GetValueAsUnsigned()
    if closure_ptr == 0:
        error_count += 1
        return False

    err = lldb.SBError()
    mat_ptr_bytes = process.ReadMemory(closure_ptr + 0x20, 8, err)
    if not err.Success() or len(mat_ptr_bytes) < 8:
        error_count += 1
        return False

    mat_ptr = struct.unpack('<Q', mat_ptr_bytes)[0]

    matrix_hits[mat_ptr] = matrix_hits.get(mat_ptr, 0) + 1

    if mat_ptr not in matrix_data and mat_ptr != 0:
        float_bytes = process.ReadMemory(mat_ptr, 36, err)
        if err.Success() and len(float_bytes) == 36:
            matrix_data[mat_ptr] = list(struct.unpack('<9f', float_bytes))
        else:
            matrix_data[mat_ptr] = None

    if hit_count % 50 == 0:
        sys.stdout.write(f"  [hit {hit_count:4d}] mat_ptr=0x{mat_ptr:016x}  distinct={len(matrix_hits)}\n")
        sys.stdout.flush()

    return False  # do not stop; continue execution


def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS_PATH, 'x86_64')
    if not target.IsValid():
        print("ERROR: Could not create target for", LRI_PROCESS_PATH)
        sys.exit(1)

    # Set DYLD_LIBRARY_PATH so libcp loads
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetEnvironmentEntries(
        [f'DYLD_LIBRARY_PATH={LIBCP_DIR}'], True
    )
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')

    err = lldb.SBError()
    process = target.Launch(launch_info, err)
    if not err.Success():
        print("ERROR launching:", err)
        sys.exit(1)

    print(f"Process launched PID={process.GetProcessID()}")

    # Wait until stopped at entry or running
    time.sleep(1)

    # Find libcp module and compute BP address
    libcp_base = None
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fn = m.GetFileSpec().GetFilename()
        if fn and 'libcp' in fn:
            load_addr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if load_addr != lldb.LLDB_INVALID_ADDRESS:
                libcp_base = load_addr
                print(f"libcp module: {m.GetFileSpec().GetFilename()}  base=0x{libcp_base:016x}")
                break

    if libcp_base is None:
        print("ERROR: libcp module not loaded yet; trying file-offset BP")
        # Fall back: find via symbol
        # Set BP by module+offset
        bp = target.BreakpointCreateByAddress(0)  # placeholder
    else:
        bp_addr = libcp_base + ICS_OFFSET
        print(f"Setting BP at 0x{bp_addr:016x} (libcp+0x{ICS_OFFSET:x})")
        bp = target.BreakpointCreateByAddress(bp_addr)

    if not bp.IsValid():
        print("ERROR: breakpoint not valid")
        sys.exit(1)

    bp.SetCallback(ics_callback)
    print(f"BP ID={bp.GetID()}  locations={bp.GetNumLocations()}")

    # Continue execution
    process.Continue()

    # Wait for process to finish
    print("Waiting for process to complete (may take several minutes)...")
    max_wait = 900  # 15 minutes
    interval = 2
    elapsed = 0

    while elapsed < max_wait:
        state = process.GetState()
        if state in (lldb.eStateExited, lldb.eStateCrashed, lldb.eStateDetached):
            print(f"Process ended: state={debugger.StateAsCString(state)}")
            break
        if state == lldb.eStateStopped:
            # Hit a real stop (signal, exception) - not a BP callback stop
            # In async mode with callback returning False, this shouldn't happen
            # but if it does, continue
            thread = process.GetSelectedThread()
            stop_reason = thread.GetStopReason()
            if stop_reason == lldb.eStopReasonBreakpoint:
                # Callback didn't auto-continue; manually continue
                process.Continue()
            else:
                print(f"Unexpected stop reason={stop_reason}; continuing")
                process.Continue()
        time.sleep(interval)
        elapsed += interval
        if elapsed % 30 == 0:
            print(f"  ... {elapsed}s elapsed, hits so far: {hit_count}")

    if elapsed >= max_wait:
        print("TIMEOUT: killing process")
        process.Kill()

    # Print summary
    print()
    print("=" * 60)
    print(f"VERDICT: ICS::$_0 @libcp+0x{ICS_OFFSET:x} 70mm = {hit_count} hits; {len(matrix_hits)} distinct CCM matrices")
    print(f"Errors during probe: {error_count}")
    print()

    for rank, (ptr, count) in enumerate(sorted(matrix_hits.items(), key=lambda x: -x[1])):
        print(f"Matrix {rank+1}: ptr=0x{ptr:016x}  hits={count}")
        floats = matrix_data.get(ptr)
        if floats is not None:
            print(f"  Row 0: [{floats[0]:+.6f}, {floats[1]:+.6f}, {floats[2]:+.6f}]")
            print(f"  Row 1: [{floats[3]:+.6f}, {floats[4]:+.6f}, {floats[5]:+.6f}]")
            print(f"  Row 2: [{floats[6]:+.6f}, {floats[7]:+.6f}, {floats[8]:+.6f}]")
        else:
            print(f"  (matrix read failed or ptr=NULL)")
        print()

    debugger.Terminate()


if __name__ == '__main__':
    main()
