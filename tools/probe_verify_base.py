#!/usr/bin/env python3
"""
Definitive probe: stop at _main, find actual libcp load address,
verify bytes at LinearizeAndColorScale, then set address-based bp
and check if it fires during L16_03434 render.

Key fix: use GetSectionLoadAddress on __TEXT section rather than
GetObjectFileHeaderAddress, which can return the file's preferred
load address instead of the actual Rosetta-translated runtime address.
"""
import lldb
import time
import struct

LRI_PATH = '/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri'
OUT_PATH = '/tmp/probe_verify.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

LINEARIZE_OFFSET = 0x352ce0  # confirmed 55 48 89 e5 at file offset

def wait_for_state(process, target_state, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = process.GetState()
        if st == target_state:
            return True
        if st in (lldb.eStateExited, lldb.eStateCrashed, lldb.eStateDetached):
            return False
        time.sleep(0.05)
    return False

def get_libcp_base_via_section(target, libcp_module):
    """Get load address via __TEXT section — most reliable method."""
    text_section = libcp_module.FindSection("__TEXT")
    if text_section.IsValid():
        load_addr = text_section.GetLoadAddress(target)
        if load_addr != lldb.LLDB_INVALID_ADDRESS:
            return load_addr
    return None

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Launch with stop at entry
    error = lldb.SBError()
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    process = target.Launch(launch_info, error)
    if error.Fail():
        print(f"Launch error: {error.GetCString()}")
        return

    print(f"PID: {process.GetProcessID()}")

    # Wait for entry stop
    if not wait_for_state(process, lldb.eStateStopped, timeout=15):
        print("ERROR: never stopped at entry")
        process.Kill()
        return

    print(f"Stopped at entry. State: {process.GetState()}")

    # Set bp at _main by symbol name (in lri_process)
    bp_main = target.BreakpointCreateByName("main", LRI_PROCESS)
    print(f"bp_main (by name): valid={bp_main.IsValid()}, locs={bp_main.GetNumLocations()}")
    if bp_main.GetNumLocations() == 0:
        # Fallback: fixed offset
        for m in target.module_iter():
            if 'lri_process' in str(m.GetFileSpec().GetFilename()):
                lri_base = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
                bp_main = target.BreakpointCreateByAddress(lri_base + 0x820)
                print(f"  Fallback bp_main at lri_base+0x820 = 0x{lri_base+0x820:x}: locs={bp_main.GetNumLocations()}")
                break

    # Continue to _main
    process.Continue()
    if not wait_for_state(process, lldb.eStateStopped, timeout=20):
        st = process.GetState()
        print(f"ERROR: didn't stop at _main (state={st})")
        process.Kill()
        return

    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    print(f"\nAt _main: PC=0x{frame.GetPC():x}, func={frame.GetFunctionName()}")

    # Delete _main bp
    target.BreakpointDelete(bp_main.GetID())

    # Enumerate all modules — look for libcp
    print("\n=== ALL LOADED MODULES ===")
    libcp_module = None
    libcp_base_hdr = None
    libcp_base_section = None

    for m in target.module_iter():
        fname = str(m.GetFileSpec().GetFilename())
        fdir = str(m.GetFileSpec().GetDirectory())
        hdr_addr = m.GetObjectFileHeaderAddress()
        hdr_load = hdr_addr.GetLoadAddress(target)

        # Get __TEXT section address
        text_sec = m.FindSection("__TEXT")
        text_load = text_sec.GetLoadAddress(target) if text_sec.IsValid() else lldb.LLDB_INVALID_ADDRESS

        if 'libcp' in fname and 'libcpan' not in fname:
            libcp_module = m
            libcp_base_hdr = hdr_load
            if text_load != lldb.LLDB_INVALID_ADDRESS:
                libcp_base_section = text_load
            print(f"  *** LIBCP: {fdir}/{fname}")
            print(f"       header_load_addr = 0x{hdr_load:x}")
            print(f"       __TEXT section   = 0x{text_load:x}" if text_load != lldb.LLDB_INVALID_ADDRESS else "       __TEXT section   = INVALID")
            # Also try via LLDB image list equivalent
            # Count sections
            num_sec = m.GetNumSections()
            print(f"       num_sections     = {num_sec}")
            for i in range(min(5, num_sec)):
                sec = m.GetSectionAtIndex(i)
                sec_load = sec.GetLoadAddress(target)
                print(f"       section[{i}] '{sec.GetName()}': load=0x{sec_load:x}" if sec_load != lldb.LLDB_INVALID_ADDRESS else f"       section[{i}] '{sec.GetName()}': INVALID")
        elif 'lri' in fname.lower() or 'light' in fname.lower() or 'rosetta' in fname.lower():
            print(f"  {fname}: hdr=0x{hdr_load:x}, __TEXT=0x{text_load:x}" if text_load != lldb.LLDB_INVALID_ADDRESS else f"  {fname}: hdr=0x{hdr_load:x}")

    if libcp_module is None:
        print("\nERROR: libcp module not found!")
        # List all modules
        for m in target.module_iter():
            fname = str(m.GetFileSpec().GetFilename())
            hdr_load = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            print(f"  {fname}: 0x{hdr_load:x}")
        process.Kill()
        return

    # Determine best base address
    # For x86_64 binary under Rosetta: the __TEXT section load address
    # should match the actual mapped address
    if libcp_base_section is not None:
        libcp_base = libcp_base_section
        print(f"\nUsing __TEXT section base: 0x{libcp_base:x}")
    else:
        libcp_base = libcp_base_hdr
        print(f"\nUsing header load addr (fallback): 0x{libcp_base:x}")

    # Compute LinearizeAndColorScale address
    lin_addr = libcp_base + LINEARIZE_OFFSET
    print(f"LinearizeAndColorScale target: libcp+0x{LINEARIZE_OFFSET:x} = 0x{lin_addr:x}")

    # Read bytes at that address to verify
    err = lldb.SBError()
    mem = process.ReadMemory(lin_addr, 16, err)
    if err.Success():
        b = bytes(mem)
        print(f"Bytes at 0x{lin_addr:x}: {b.hex()}")
        if b[:4] == bytes([0x55, 0x48, 0x89, 0xe5]):
            print("  VERIFIED: 55 48 89 e5 = push rbp; mov rbp, rsp (correct x86_64 prologue)")
        else:
            print(f"  WARNING: Expected 55 48 89 e5, got {b[:4].hex()}")
            # Try other candidate bases
            print("\n  Trying alternative base calculations:")
            for alt_name, alt_base in [
                ("hdr_base", libcp_base_hdr),
                ("hdr_base-0x100000000", libcp_base_hdr - 0x100000000 if libcp_base_hdr else 0),
            ]:
                if alt_base and alt_base != libcp_base:
                    alt_addr = alt_base + LINEARIZE_OFFSET
                    mem2 = process.ReadMemory(alt_addr, 4, err)
                    if err.Success():
                        b2 = bytes(mem2)
                        print(f"    {alt_name}=0x{alt_base:x}: bytes={b2.hex()} {'MATCH' if b2[:4]==bytes([0x55,0x48,0x89,0xe5]) else ''}")
    else:
        print(f"Cannot read memory at 0x{lin_addr:x}: {err.GetCString()}")
        # Memory not mapped? Try brute-force search
        print("\nSearching for 55 48 89 e5 pattern near expected offsets...")
        # Try a range of potential bases
        search_bases = [
            0x100000000,
            0x108c7a000,
            libcp_base_hdr,
        ]
        if libcp_base_hdr > 0x100000000:
            search_bases.append(libcp_base_hdr - 0x100000000)

        for sb in set(search_bases):
            if sb <= 0:
                continue
            try_addr = sb + LINEARIZE_OFFSET
            mem2 = process.ReadMemory(try_addr, 4, err)
            if err.Success():
                b2 = bytes(mem2)
                match = b2[:4] == bytes([0x55, 0x48, 0x89, 0xe5])
                print(f"  base=0x{sb:x} -> 0x{try_addr:x}: {b2.hex()} {'MATCH!' if match else ''}")

    # Also search a broad range of memory for the 4-byte signature of LinearizeAndColorScale
    # This helps us find the actual load address if the module reports wrong
    print("\nSearching process memory for LinearizeAndColorScale signature...")
    print("(looking for bytes 55 48 89 e5 at offsets that match 0x352ce0 pattern)")
    # We know the file offset is 0x352ce0; the last 3 bytes (0x52ce0 = 339168) should
    # be preserved in load address if ASLR only adds to the high bits
    # Try reading at known-good region addresses
    target_pattern = bytes([0x55, 0x48, 0x89, 0xe5])

    # Scan memory regions near libcp header
    for base_candidate in [0x100000000, 0x108000000, 0x108c7a000, 0x110000000]:
        addr_candidate = base_candidate + LINEARIZE_OFFSET
        mem3 = process.ReadMemory(addr_candidate, 4, err)
        if err.Success() and bytes(mem3)[:4] == target_pattern:
            print(f"  FOUND at base=0x{base_candidate:x}, lin_addr=0x{addr_candidate:x}: {bytes(mem3).hex()}")
            libcp_base = base_candidate
            lin_addr = addr_candidate

    # Now set the breakpoint at the verified address
    print(f"\nSetting bp at LinearizeAndColorScale (0x{lin_addr:x})...")
    bp_lin = target.BreakpointCreateByAddress(lin_addr)
    print(f"  bp_lin: valid={bp_lin.IsValid()}, locs={bp_lin.GetNumLocations()}")

    # Also set at AWB kernel
    awb_addr = libcp_base + 0x3510f0
    bp_awb = target.BreakpointCreateByAddress(awb_addr)
    print(f"  bp_awb (0x3510f0): valid={bp_awb.IsValid()}, locs={bp_awb.GetNumLocations()}")

    # And at the lambda entry 0x342730
    lambda_addr = libcp_base + 0x342730
    bp_lambda = target.BreakpointCreateByAddress(lambda_addr)
    print(f"  bp_lambda (0x342730): valid={bp_lambda.IsValid()}, locs={bp_lambda.GetNumLocations()}")

    # And at 0x350ff0 (caller of LinearizeAndColorScale)
    caller_addr = libcp_base + 0x350ff0
    bp_caller = target.BreakpointCreateByAddress(caller_addr)
    print(f"  bp_caller (0x350ff0): valid={bp_caller.IsValid()}, locs={bp_caller.GetNumLocations()}")

    bps = {
        bp_lin.GetID(): 'LinearizeAndColorScale+0x352ce0',
        bp_awb.GetID(): 'AWBkernel+0x3510f0',
        bp_lambda.GetID(): 'lambda+0x342730',
        bp_caller.GetID(): 'caller+0x350ff0',
    }

    print(f"\nContinuing. Process will render L16_03434 (takes ~2 min)...")
    process.Continue()

    deadline = time.time() + 180  # 3 minutes
    hit_log = []

    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            reason = thread.GetStopReason()

            if reason == lldb.eStopReasonBreakpoint:
                bp_id = thread.GetStopReasonDataAtIndex(0)
                name = bps.get(bp_id, f'bp_{bp_id}')
                offset = pc - libcp_base
                fname = frame.GetFunctionName() or "??"
                rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
                rsi = frame.FindRegister("rsi").GetValueAsUnsigned()

                entry = f"HIT: {name} PC=0x{pc:x} libcp+0x{offset:x} func={fname} rdi=0x{rdi:x} rsi=0x{rsi:x}"
                print(f"\n*** {entry} ***")

                # Print stack
                for i in range(min(6, thread.GetNumFrames())):
                    f = thread.GetFrameAtIndex(i)
                    foff = f.GetPC() - libcp_base
                    print(f"  [{i}] libcp+0x{foff:x} {f.GetFunctionName()}")

                hit_log.append(entry)
                if len(hit_log) >= 5:
                    print("5 hits reached, stopping")
                    break
                process.Continue()

            elif reason == lldb.eStopReasonSignal:
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"  Stop reason={reason} at 0x{pc:x}")
                process.Continue()

        elif st == lldb.eStateExited:
            code = process.GetExitStatus()
            print(f"\nProcess exited (code={code}). Hits: {len(hit_log)}")
            if not hit_log:
                print("ZERO breakpoint hits — breakpoints did not fire")
            break
        elif st == lldb.eStateCrashed:
            print("CRASHED")
            break
        else:
            time.sleep(0.1)

    print("\n=== SUMMARY ===")
    for h in hit_log:
        print(f"  {h}")
    if not hit_log:
        print("  NO HITS")

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("Done.")

if __name__ == '__main__':
    run()
