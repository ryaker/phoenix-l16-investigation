#!/usr/bin/env python3
"""
Auto-watchpoint script for finding WB gain write site.
Run from lldb: command script import /path/to/auto_wb_watchpoint.py
Then: run_wb_trace
"""
import lldb

LIBCP_OFFSET_LINEARIZE = 0x352ce0  # LinearizeAndColorScale setup
LIBCP_OFFSET_AWB_KERNEL = 0x3510f0  # AWB kernel (reads ctx[0..8])

g_ctx_addr = None
g_libcp_base = None

def get_libcp_base(target):
    for module in target.module_iter():
        name = str(module.GetFileSpec().GetFilename())
        if 'libcp' in name and 'libcpan' not in name:
            header_addr = module.GetObjectFileHeaderAddress()
            load_addr = header_addr.GetLoadAddress(target)
            return load_addr
    return None

def on_linearize_breakpoint(frame, bp_loc, extra_args, internal_dict):
    """Called when LinearizeAndColorScale setup is hit"""
    global g_ctx_addr, g_libcp_base

    target = frame.GetThread().GetProcess().GetTarget()

    # Get filter_obj from rdi
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()

    # Dereference filter_obj to get ctx pointer
    error = lldb.SBError()
    process = frame.GetThread().GetProcess()
    ctx_ptr = process.ReadPointerFromMemory(rdi, error)

    if error.Success():
        g_ctx_addr = ctx_ptr
        print(f"\n[WB_TRACE] LinearizeAndColorScale hit!")
        print(f"[WB_TRACE] filter_obj (rdi) = 0x{rdi:x}")
        print(f"[WB_TRACE] ctx = *(filter_obj) = 0x{ctx_ptr:x}")

        # Read current ctx[0], ctx[4], ctx[8]
        v0 = process.ReadMemory(ctx_ptr, 4, error)
        v4 = process.ReadMemory(ctx_ptr + 4, 4, error)
        v8 = process.ReadMemory(ctx_ptr + 8, 4, error)

        import struct
        f0 = struct.unpack('<f', v0)[0]
        f4 = struct.unpack('<f', v4)[0]
        f8 = struct.unpack('<f', v8)[0]
        print(f"[WB_TRACE] ctx[0]=0x{ctx_ptr:x} = {f0:.7f} (should be 1/R_gain)")
        print(f"[WB_TRACE] ctx[4]=0x{ctx_ptr+4:x} = {f4:.7f} (should be 1.0)")
        print(f"[WB_TRACE] ctx[8]=0x{ctx_ptr+8:x} = {f8:.7f} (should be 1/B_gain)")

        # Set write watchpoint on ctx[0]
        wp = target.WatchAddress(ctx_ptr, 4, False, True, error)
        if error.Success():
            print(f"[WB_TRACE] Watchpoint set on ctx[0] = 0x{ctx_ptr:x}")
            wp.SetCallback(on_watchpoint_hit, None)
        else:
            print(f"[WB_TRACE] Watchpoint failed: {error.GetCString()}")

        # Disable this breakpoint so we don't loop
        bp_loc.GetBreakpoint().SetEnabled(False)

        # Continue
        return False  # Don't stop
    else:
        print(f"[WB_TRACE] Failed to read ctx pointer: {error.GetCString()}")
        return True

def on_watchpoint_hit(frame, wp_loc, extra_args, internal_dict):
    """Called when ctx[0] is written"""
    print("\n[WB_TRACE] *** WRITE to ctx[0] DETECTED! ***")

    # Get thread and frame info
    thread = frame.GetThread()
    process = thread.GetProcess()

    print(f"[WB_TRACE] PC = 0x{frame.GetPC():x}")
    print(f"[WB_TRACE] Function: {frame.GetFunctionName()}")

    # Print full call stack
    print("[WB_TRACE] Call stack:")
    for i in range(min(15, thread.GetNumFrames())):
        f = thread.GetFrameAtIndex(i)
        print(f"  [{i}] 0x{f.GetPC():x} {f.GetFunctionName()}")

    # Read register values
    print(f"[WB_TRACE] Registers at write:")
    for reg_name in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rsp', 'rbp', 'r12', 'r13', 'r14', 'r15']:
        reg = frame.FindRegister(reg_name)
        if reg.IsValid():
            print(f"  {reg_name} = 0x{reg.GetValueAsUnsigned():x}")

    # Read xmm registers (the value being written)
    for xmm in ['xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4']:
        reg = frame.FindRegister(xmm)
        if reg.IsValid():
            import struct
            raw = reg.GetData().GetBytes()
            if len(raw) >= 4:
                f = struct.unpack('<f', bytes(raw[:4]))[0]
                print(f"  {xmm}[0] = {f:.7f}")

    # Read what was just written to ctx[0]
    error = lldb.SBError()
    v0 = process.ReadMemory(g_ctx_addr, 4, error)
    import struct
    f0 = struct.unpack('<f', v0)[0]
    print(f"[WB_TRACE] New ctx[0] value = {f0:.7f}")

    return True  # Stop execution so we can inspect

def run_wb_trace(debugger, command, result, internal_dict):
    global g_libcp_base

    target = debugger.GetSelectedTarget()

    # First run to get module layout
    print("[WB_TRACE] Launching process to find libcp base...")

    # Set an early breakpoint at main to get the layout
    bp_main = target.BreakpointCreateByName("main")

    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([
        '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri',
        '/tmp/test_wb_out.tiff'
    ])

    process = target.Launch(launch_info, error)
    if error.Fail():
        print(f"Launch failed: {error.GetCString()}")
        return

    # Wait for main breakpoint
    process.GetSelectedThread().WaitForStop()

    # Now get libcp base
    g_libcp_base = get_libcp_base(target)
    if g_libcp_base is None:
        print("[WB_TRACE] Could not find libcp! Continuing...")
        process.Continue()
        return

    print(f"[WB_TRACE] libcp base: 0x{g_libcp_base:x}")
    linearize_addr = g_libcp_base + LIBCP_OFFSET_LINEARIZE
    print(f"[WB_TRACE] LinearizeAndColorScale at: 0x{linearize_addr:x}")

    # Remove main breakpoint, set at LinearizeAndColorScale
    target.BreakpointDelete(bp_main.GetID())

    bp_linearize = target.BreakpointCreateByAddress(linearize_addr)
    bp_linearize.SetScriptCallbackFunction("auto_wb_watchpoint.on_linearize_breakpoint")

    print("[WB_TRACE] Breakpoint set, continuing...")
    process.Continue()

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f auto_wb_watchpoint.run_wb_trace run_wb_trace')
    print("[WB_TRACE] Module loaded. Use 'run_wb_trace' command.")
