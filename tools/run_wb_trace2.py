#!/usr/bin/env python3
"""
LLDB Python API script v2 - uses stop-at-entry approach
"""
import lldb
import struct
import sys
import time
import os

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/test_wb_python2.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

# File offsets in libcp
LINEARIZE_OFFSET = 0x352ce0
AWB_KERNEL_OFFSET = 0x3510f0

def wait_for_stop(process, timeout_sec=120):
    """Wait until process stops or exits"""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        state = process.GetState()
        if state == lldb.eStateStopped:
            return 'stopped'
        if state == lldb.eStateExited:
            return 'exited'
        if state == lldb.eStateCrashed:
            return 'crashed'
        time.sleep(0.05)
    return 'timeout'

def get_float32(process, addr):
    err = lldb.SBError()
    data = process.ReadMemory(addr, 4, err)
    if err.Success():
        return struct.unpack('<f', data)[0]
    return None

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: Could not create target")
        return

    print(f"Target: {LRI_PROCESS}")

    # Create breakpoint at main
    MAIN_ADDR = 0x100000820
    bp_main = target.BreakpointCreateByAddress(MAIN_ADDR)
    print(f"Breakpoint at main (0x{MAIN_ADDR:x}): valid={bp_main.IsValid()}, locations={bp_main.GetNumLocations()}")

    # Launch with stop at entry
    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    process = target.Launch(launch_info, error)
    if error.Fail():
        print(f"Launch failed: {error.GetCString()}")
        return

    print(f"Process launched: PID {process.GetProcessID()}")

    # Wait for stop at entry
    result = wait_for_stop(process, timeout_sec=10)
    print(f"Initial stop result: {result}")

    if result == 'stopped':
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()
        print(f"Stopped at entry: 0x{frame.GetPC():x}")

        # Now image list
        print("\nModules loaded:")
        libcp_base = None
        for module in target.module_iter():
            name = str(module.GetFileSpec().GetFilename())
            if 'libcp' in name:
                hdr = module.GetObjectFileHeaderAddress()
                base = hdr.GetLoadAddress(target)
                libcp_base = base
                print(f"  {name}: base=0x{base:x}")

        if libcp_base is None:
            print("  libcp NOT loaded yet at entry")

        # Set breakpoint at LinearizeAndColorScale using file offset
        # We need to know libcp base - it might not be loaded yet
        # Let's try with the known fixed address
        KNOWN_LIBCP_BASE = 0x108c7a000  # from prior run with ASLR disabled
        linearize_addr = KNOWN_LIBCP_BASE + LINEARIZE_OFFSET
        print(f"\nSetting bp at LinearizeAndColorScale: 0x{linearize_addr:x}")
        bp_lin = target.BreakpointCreateByAddress(linearize_addr)
        print(f"  valid={bp_lin.IsValid()}, locations={bp_lin.GetNumLocations()}")

        # Remove main bp
        target.BreakpointDelete(bp_main.GetID())

        # Continue to LinearizeAndColorScale
        print("Continuing...")
        process.Continue()
        result = wait_for_stop(process, timeout_sec=120)
        print(f"Next stop: {result}")

        if result == 'stopped':
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            print(f"Stopped at: 0x{pc:x}")

            if pc == linearize_addr or abs(pc - linearize_addr) < 10:
                print("HIT: LinearizeAndColorScale!")
                rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
                print(f"  rdi = 0x{rdi:x}")

                err = lldb.SBError()
                ctx_ptr = process.ReadPointerFromMemory(rdi, err)
                if err.Success():
                    print(f"  ctx_ptr = 0x{ctx_ptr:x}")
                    f0 = get_float32(process, ctx_ptr)
                    f4 = get_float32(process, ctx_ptr + 4)
                    f8 = get_float32(process, ctx_ptr + 8)
                    print(f"  ctx[0]={f0}, ctx[4]={f4}, ctx[8]={f8}")

                    # Watchpoint on ctx[0]
                    err2 = lldb.SBError()
                    wp = target.WatchAddress(ctx_ptr, 4, False, True, err2)
                    if err2.Success():
                        print(f"  Watchpoint set on 0x{ctx_ptr:x}")
                    else:
                        print(f"  Watchpoint error: {err2.GetCString()}")
                else:
                    print(f"  Read pointer error: {err.GetCString()}")
            else:
                print(f"Unexpected stop at 0x{pc:x}")
                # Print backtrace
                for i in range(min(10, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    print(f"  [{i}] 0x{f.GetPC():x}")

        elif result == 'exited':
            print("Process exited - breakpoint not hit")

    lldb.SBDebugger.Destroy(debugger)

if __name__ == '__main__':
    run()
