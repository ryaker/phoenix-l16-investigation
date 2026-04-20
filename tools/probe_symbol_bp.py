#!/usr/bin/env python3
"""
Set breakpoints by SYMBOL NAME (not address) so LLDB resolves them when dylibs load.
This avoids the address-calculation problem entirely.
"""
import lldb
import time
import struct

LRI_PATH = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH = '/tmp/probe_symbol.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

LIBCP = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib'

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    # Load libcp as a module so LLDB knows about its symbols
    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Add libcp as a module to search
    # Set bp by searching for functions containing known substrings
    # First, try address-based but from the file spec + offset

    # Load libcp as an extra image
    spec = lldb.SBFileSpec(LIBCP, True)
    print(f"Loading libcp module...")

    # Try BreakpointCreateByRegex to find functions
    bp_lin = target.BreakpointCreateByRegex("LinearizeAndColorScale")
    print(f"bp LinearizeAndColorScale by name: valid={bp_lin.IsValid()}, locs={bp_lin.GetNumLocations()}")

    bp_awb = target.BreakpointCreateByRegex("awb_kernel|AWBKernel|ApplyAWB")
    print(f"bp awb_kernel by regex: valid={bp_awb.IsValid()}, locs={bp_awb.GetNumLocations()}")

    bp_wb = target.BreakpointCreateByRegex("WhiteBalance|whitebalance|white_balance")
    print(f"bp WhiteBalance by regex: valid={bp_wb.IsValid()}, locs={bp_wb.GetNumLocations()}")

    bp_setgain = target.BreakpointCreateByRegex("SetGain|setGain|set_gain|ChannelGain")
    print(f"bp SetGain by regex: valid={bp_setgain.IsValid()}, locs={bp_setgain.GetNumLocations()}")

    # Launch
    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                   '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    if not process or not process.IsValid():
        print("Launch failed")
        return

    print(f"\nPID: {process.GetProcessID()}")

    # Wait for process to run and check module loading
    time.sleep(2)

    # Re-check bp locations after modules loaded
    print(f"\nAfter launch bp locations:")
    print(f"  LinearizeAndColorScale: {bp_lin.GetNumLocations()}")
    print(f"  awb_kernel regex: {bp_awb.GetNumLocations()}")
    print(f"  WhiteBalance regex: {bp_wb.GetNumLocations()}")
    print(f"  SetGain regex: {bp_setgain.GetNumLocations()}")

    # List all modules
    print("\nAll modules:")
    libcp_base = None
    for m in target.module_iter():
        name = str(m.GetFileSpec().GetFilename())
        base = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
        print(f"  {name}: 0x{base:x}")
        if 'libcp' in name and 'libcpan' not in name:
            libcp_base = base

    if libcp_base:
        print(f"\nlibcp base: 0x{libcp_base:x}")
        # Set address-based bps now
        lin_addr = libcp_base + 0x352ce0
        awb_addr = libcp_base + 0x3510f0
        print(f"  LinearizeAndColorScale at: 0x{lin_addr:x}")

        # Verify bytes
        err = lldb.SBError()
        b = process.ReadMemory(lin_addr, 4, err)
        if err.Success():
            print(f"  Bytes: {bytes(b).hex()} (expect 55 48 89 e5)")
        else:
            print(f"  Cannot read: {err.GetCString()}")

        # Check module's symbol table for LinearizeAndColorScale
        libcp_module = None
        for m in target.module_iter():
            if 'libcp' in str(m.GetFileSpec().GetFilename()) and 'libcpan' not in str(m.GetFileSpec().GetFilename()):
                libcp_module = m
                break

        if libcp_module:
            print(f"\nSearching libcp symbols for 'Linearize':")
            sym_ctx_list = libcp_module.FindFunctions("LinearizeAndColorScale", lldb.eFunctionNameTypeAny)
            print(f"  Found {sym_ctx_list.GetSize()} matches")
            for i in range(sym_ctx_list.GetSize()):
                ctx = sym_ctx_list.GetContextAtIndex(i)
                func = ctx.GetFunction()
                if func.IsValid():
                    start = func.GetStartAddress().GetLoadAddress(target)
                    print(f"  {func.GetName()}: 0x{start:x}")

            # Try symbol search
            print("\nSymbol search for 'Linearize':")
            sym_list = libcp_module.FindSymbols("LinearizeAndColorScale", lldb.eSymbolTypeAny)
            print(f"  Found {sym_list.GetSize()} symbols")
            for i in range(min(10, sym_list.GetSize())):
                sym = sym_list.GetContextAtIndex(i).GetSymbol()
                if sym.IsValid():
                    addr = sym.GetStartAddress().GetLoadAddress(target)
                    print(f"  {sym.GetName()}: 0x{addr:x}")

            # List a few functions in the right address range
            print("\nFunctions near 0x352ce0:")
            count = 0
            for i in range(libcp_module.GetNumSymbols()):
                sym = libcp_module.GetSymbolAtIndex(i)
                start = sym.GetStartAddress().GetFileAddress()
                if 0x350000 < start < 0x355000:
                    load_addr = sym.GetStartAddress().GetLoadAddress(target)
                    print(f"  0x{start:x} (load: 0x{load_addr:x}): {sym.GetName()}")
                    count += 1
                if count > 20:
                    break

    # Wait for process to exit
    deadline = time.time() + 120
    stop_count = 0
    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            reason = thread.GetStopReason()
            if reason == lldb.eStopReasonBreakpoint:
                stop_count += 1
                bp_id = thread.GetStopReasonDataAtIndex(0)
                print(f"\n*** BP HIT #{stop_count}: PC=0x{pc:x}, bp_id={bp_id} ***")
                print(f"  Function: {frame.GetFunctionName()}")
                if libcp_base:
                    print(f"  Offset: libcp+0x{pc - libcp_base:x}")
                # Backtrace
                for i in range(min(6, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    off = (f.GetPC() - libcp_base) if libcp_base else 0
                    print(f"  [{i}] libcp+0x{off:x} {f.GetFunctionName()}")
                if stop_count >= 5:
                    break
                process.Continue()
            elif reason == lldb.eStopReasonSignal:
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"  Stop reason={reason} at 0x{pc:x}")
                process.Continue()
        elif st == lldb.eStateExited:
            print(f"\nExited. BP hits: {stop_count}")
            break
        elif st == lldb.eStateCrashed:
            print("CRASHED")
            break
        else:
            time.sleep(0.1)

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("Done.")

if __name__ == '__main__':
    run()
