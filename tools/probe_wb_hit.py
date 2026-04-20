#!/usr/bin/env python3
"""
Set breakpoints by regex on WhiteBalance and SetGain functions.
Find which ones actually fire during lri_process execution.
Also set bps on Renderer::render and related exported symbols.
"""
import lldb
import time
import struct

LRI_PATH = '/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri'
OUT_PATH = '/tmp/probe_wb_hit_03434.tiff'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'

def run():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTarget(LRI_PROCESS)
    if not target.IsValid():
        print("ERROR: target invalid")
        return

    # Set named breakpoints before launch so LLDB resolves them as libs load
    bp_wb = target.BreakpointCreateByRegex("WhiteBalance")
    bp_setgain = target.BreakpointCreateByRegex("SetGain")
    bp_renderer_render = target.BreakpointCreateByName("__ZN5CIAPI8Renderer6renderEiRKNS_3ROIENS_10RenderTypeEb")
    bp_apply_tuning = target.BreakpointCreateByName("__ZN5CIAPI11ApplyTuningENS_10TuningTypeERNS_12RendererBaseE")
    bp_deserialize = target.BreakpointCreateByName("__ZN5CIAPI8Renderer11deserializeERKNSt3__110shared_ptrINS1_13basic_istreamIcNS1_11char_traitsIcEEEEEENS_9StateTypeE")

    print(f"Pre-launch bp counts:")
    print(f"  WhiteBalance: {bp_wb.GetNumLocations()}")
    print(f"  SetGain: {bp_setgain.GetNumLocations()}")
    print(f"  Renderer::render: {bp_renderer_render.GetNumLocations()}")
    print(f"  ApplyTuning: {bp_apply_tuning.GetNumLocations()}")
    print(f"  deserialize: {bp_deserialize.GetNumLocations()}")

    # List WhiteBalance bp locations
    print(f"\nWhiteBalance bp locations:")
    for i in range(bp_wb.GetNumLocations()):
        loc = bp_wb.GetLocationAtIndex(i)
        addr = loc.GetAddress().GetFileAddress()
        print(f"  [{i}] 0x{addr:x}")

    # Launch
    process = target.LaunchSimple([LRI_PATH, OUT_PATH], None,
                                   '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    if not process or not process.IsValid():
        print("Launch failed")
        return

    print(f"\nPID: {process.GetProcessID()}")
    time.sleep(2)

    print(f"\nPost-launch bp counts:")
    print(f"  WhiteBalance: {bp_wb.GetNumLocations()}")
    print(f"  SetGain: {bp_setgain.GetNumLocations()}")
    print(f"  Renderer::render: {bp_renderer_render.GetNumLocations()}")
    print(f"  ApplyTuning: {bp_apply_tuning.GetNumLocations()}")
    print(f"  deserialize: {bp_deserialize.GetNumLocations()}")

    # Get libcp base for offset display
    libcp_base = None
    for m in target.module_iter():
        name = str(m.GetFileSpec().GetFilename())
        if 'libcp' in name and 'libcpan' not in name:
            libcp_base = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break

    # Build a map of bp_id -> name
    bp_map = {
        bp_wb.GetID(): 'WhiteBalance',
        bp_setgain.GetID(): 'SetGain',
        bp_renderer_render.GetID(): 'Renderer::render',
        bp_apply_tuning.GetID(): 'ApplyTuning',
        bp_deserialize.GetID(): 'deserialize',
    }

    # Accumulate hit counts per bp location
    hit_counts = {}  # pc -> count
    first_hits = {}  # pc -> frame info

    print("\nWaiting for breakpoint hits...")
    deadline = time.time() + 120
    total_hits = 0

    while time.time() < deadline:
        st = process.GetState()
        if st == lldb.eStateStopped:
            thread = process.GetSelectedThread()
            frame = thread.GetSelectedFrame()
            pc = frame.GetPC()
            reason = thread.GetStopReason()

            if reason == lldb.eStopReasonBreakpoint:
                bp_id = thread.GetStopReasonDataAtIndex(0)
                bp_name = bp_map.get(bp_id, f'bp_{bp_id}')
                total_hits += 1
                hit_counts[pc] = hit_counts.get(pc, 0) + 1

                offset = (pc - libcp_base) if libcp_base else 0
                fname = frame.GetFunctionName() or "??"
                key = f"{bp_name}@libcp+0x{offset:x}"

                if pc not in first_hits:
                    first_hits[pc] = {
                        'bp_name': bp_name,
                        'offset': offset,
                        'fname': fname,
                        'count': 0,
                        'rdi': frame.FindRegister("rdi").GetValueAsUnsigned(),
                        'rsi': frame.FindRegister("rsi").GetValueAsUnsigned(),
                        'xmm0': None,
                    }
                    # Try to get xmm0 float
                    xmm0_reg = frame.FindRegister("xmm0")
                    if xmm0_reg.IsValid():
                        try:
                            raw = bytes(xmm0_reg.GetData().GetRawData(lldb.SBError(), 0, 4)[:4])
                            first_hits[pc]['xmm0'] = struct.unpack('<f', raw)[0]
                        except:
                            pass

                first_hits[pc]['count'] += 1

                if total_hits <= 30:
                    print(f"  HIT #{total_hits}: {bp_name} at libcp+0x{offset:x} ({fname}) rdi=0x{first_hits[pc]['rdi']:x}")
                elif total_hits == 31:
                    print(f"  (suppressing further hit output, still running...)")

                process.Continue()

            elif reason == lldb.eStopReasonSignal:
                process.Continue()
            else:
                if pc != 0xffffffffffffffff:
                    print(f"  Stop reason={reason} at 0x{pc:x}")
                process.Continue()

        elif st == lldb.eStateExited:
            print(f"\nProcess exited. Total hits: {total_hits}")
            break
        elif st == lldb.eStateCrashed:
            print("\nCrashed")
            break
        else:
            time.sleep(0.1)

    print(f"\n=== HIT SUMMARY ===")
    print(f"Total hits: {total_hits}")
    print(f"Unique addresses hit:")
    for pc, info in sorted(first_hits.items(), key=lambda x: x[1]['offset']):
        xmm_str = f" xmm0={info['xmm0']:.6f}" if info['xmm0'] is not None else ""
        print(f"  libcp+0x{info['offset']:x} x{info['count']:3d} [{info['bp_name']}] {info['fname']}{xmm_str}")

    print(f"\n=== NOT HIT ===")
    # Find which WhiteBalance locations were NOT hit
    all_wbp_pcs = set()
    for i in range(bp_wb.GetNumLocations()):
        loc = bp_wb.GetLocationAtIndex(i)
        fa = loc.GetAddress().GetLoadAddress(target)
        all_wbp_pcs.add(fa)

    not_hit = all_wbp_pcs - set(first_hits.keys())
    for pc in sorted(not_hit):
        offset = (pc - libcp_base) if libcp_base else 0
        print(f"  libcp+0x{offset:x} (not hit)")

    process.Kill()
    lldb.SBDebugger.Destroy(debugger)
    print("\nDone.")

if __name__ == '__main__':
    run()
