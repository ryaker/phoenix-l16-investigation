#!/usr/bin/env python3
"""
LLDB Python API script to catch WB gain write site.
Runs standalone using the lldb Python module.
"""
import lldb
import struct
import sys
import os

def find_wb_write_site():
    LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
    OUT_PATH = '/tmp/test_wb_python.tiff'
    LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

    # Offsets from libcp base
    LINEARIZE_OFFSET = 0x352ce0
    AWB_KERNEL_OFFSET = 0x3510f0
    MAIN_ADDR = 0x100000820  # Static address (ASLR disabled)

    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(False)  # Synchronous mode

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: Could not create target")
        return

    # Create breakpoint at main static address
    bp_main = target.BreakpointCreateByAddress(MAIN_ADDR)
    print(f"Breakpoint at main (0x{MAIN_ADDR:x}): {bp_main.IsValid()}")

    # Launch
    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')

    process = target.Launch(launch_info, error)
    if error.Fail():
        print(f"Launch failed: {error.GetCString()}")
        return

    print(f"Process launched: PID {process.GetProcessID()}")

    # Wait for main breakpoint
    event = lldb.SBEvent()
    listener = debugger.GetListener()

    # Poll for stop
    state = process.GetState()
    print(f"Initial state: {lldb.SBDebugger.StateAsCString(state)}")

    # Wait for stopped state
    for i in range(100):
        state = process.GetState()
        if state == lldb.eStateStopped:
            break
        if state == lldb.eStateExited:
            print("Process exited before hitting breakpoint!")
            return
        import time
        time.sleep(0.1)

    print(f"Process state: {lldb.SBDebugger.StateAsCString(state)}")

    if state != lldb.eStateStopped:
        print("Never stopped!")
        return

    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    print(f"Stopped at PC: 0x{frame.GetPC():x}")

    # Now get libcp base
    libcp_base = None
    for module in target.module_iter():
        name = str(module.GetFileSpec().GetFilename())
        if 'libcp' in name and 'libcpan' not in name:
            header_addr = module.GetObjectFileHeaderAddress()
            libcp_base = header_addr.GetLoadAddress(target)
            print(f"libcp base: 0x{libcp_base:x}")
            break

    if libcp_base is None:
        print("ERROR: libcp not found!")
        process.Continue()
        return

    # Set breakpoint at LinearizeAndColorScale
    linearize_addr = libcp_base + LINEARIZE_OFFSET
    awb_addr = libcp_base + AWB_KERNEL_OFFSET
    print(f"Setting breakpoint at LinearizeAndColorScale: 0x{linearize_addr:x}")

    bp_linearize = target.BreakpointCreateByAddress(linearize_addr)
    bp_awb = target.BreakpointCreateByAddress(awb_addr)
    print(f"  linearize bp valid: {bp_linearize.IsValid()}")
    print(f"  awb bp valid: {bp_awb.IsValid()}")

    # Remove main breakpoint
    target.BreakpointDelete(bp_main.GetID())

    # Continue
    print("Continuing to LinearizeAndColorScale...")
    process.Continue()

    # Wait for next stop
    for i in range(600):  # 60 seconds
        state = process.GetState()
        if state == lldb.eStateStopped:
            break
        if state == lldb.eStateExited:
            print("Process exited without hitting LinearizeAndColorScale!")
            return
        import time
        time.sleep(0.1)

    if state != lldb.eStateStopped:
        print(f"State: {lldb.SBDebugger.StateAsCString(state)}")
        return

    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    pc = frame.GetPC()
    print(f"\n*** Stopped at: 0x{pc:x} ***")
    print(f"Function: {frame.GetFunctionName()}")

    if pc == linearize_addr:
        print("Hit LinearizeAndColorScale!")
        # Get rdi = filter_obj
        rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
        print(f"  rdi (filter_obj) = 0x{rdi:x}")

        # Dereference to get ctx
        err = lldb.SBError()
        ctx_ptr = process.ReadPointerFromMemory(rdi, err)
        if err.Success():
            print(f"  ctx = *(filter_obj) = 0x{ctx_ptr:x}")

            # Read ctx[0], ctx[4], ctx[8]
            v0 = process.ReadMemory(ctx_ptr, 4, err)
            v4 = process.ReadMemory(ctx_ptr + 4, 4, err)
            v8 = process.ReadMemory(ctx_ptr + 8, 4, err)
            f0 = struct.unpack('<f', v0)[0]
            f4 = struct.unpack('<f', v4)[0]
            f8 = struct.unpack('<f', v8)[0]
            print(f"  ctx[0] = {f0:.7f}")
            print(f"  ctx[4] = {f4:.7f}")
            print(f"  ctx[8] = {f8:.7f}")

            # Set watchpoint on ctx[0]
            err2 = lldb.SBError()
            wp = target.WatchAddress(ctx_ptr, 4, False, True, err2)
            if err2.Success():
                print(f"\nWatchpoint set on ctx[0] = 0x{ctx_ptr:x}")
            else:
                print(f"Watchpoint failed: {err2.GetCString()}")

    elif pc == awb_addr:
        print("Hit AWB kernel!")
        # Read rax = ctx (from earlier analysis)
        rax = frame.FindRegister("rax").GetValueAsUnsigned()
        print(f"  rax = 0x{rax:x}")

    # Remove breakpoints and continue
    target.BreakpointDelete(bp_linearize.GetID())
    target.BreakpointDelete(bp_awb.GetID())
    process.Continue()

    # Wait for watchpoint hit or completion
    print("Waiting for watchpoint or completion...")
    for i in range(600):
        state = process.GetState()
        if state == lldb.eStateStopped:
            break
        if state == lldb.eStateExited:
            print("Process exited - no watchpoint hit")
            return
        import time
        time.sleep(0.1)

    if state == lldb.eStateStopped:
        thread = process.GetSelectedThread()
        frame = thread.GetSelectedFrame()
        pc = frame.GetPC()
        print(f"\n*** Watchpoint/Breakpoint hit at: 0x{pc:x} ***")
        print(f"Offset from libcp: +0x{pc - libcp_base:x}")
        print(f"Function: {frame.GetFunctionName()}")

        # Print call stack
        print("Call stack:")
        for i in range(min(20, thread.GetNumFrames())):
            f = thread.GetFrameAtIndex(i)
            print(f"  [{i}] 0x{f.GetPC():x} (libcp+0x{f.GetPC()-libcp_base:x}) {f.GetFunctionName()}")

        # Print registers
        print("Key registers:")
        for reg_name in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'r12', 'r13', 'r14', 'r15']:
            reg = frame.FindRegister(reg_name)
            if reg.IsValid():
                val = reg.GetValueAsUnsigned()
                print(f"  {reg_name} = 0x{val:x}")

        # XMM registers (the value being written)
        for xmm in ['xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4']:
            reg = frame.FindRegister(xmm)
            if reg.IsValid():
                data = reg.GetData()
                if data.GetByteSize() >= 4:
                    err3 = lldb.SBError()
                    raw = data.ReadRawData(err3, 0, 4)
                    if raw and len(raw) >= 4:
                        f = struct.unpack('<f', bytes(raw[:4]))[0]
                        print(f"  {xmm}[f32] = {f:.7f}")

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)

if __name__ == '__main__':
    find_wb_write_site()
