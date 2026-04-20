#!/usr/bin/env python3
"""
35mm depth probe v5 — event loop approach, BPs set IMMEDIATELY at entry stop.

No async window at all. If libcp not at entry, walk dyld-loaded list with retries.
Uses async mode + listener for event-driven processing without blocking.
Terminates after Triangulator settles (>5s with no new hits).

Run: arch -x86_64 /usr/bin/python3 probe_depth_35mm_v5.py
"""

import sys
import struct
import time
import collections

LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)

import lldb

LRI_PATH    = '/Volumes/Base Photos/Light/2018-10-25/L16_02951.lri'
OUT_PATH    = '/tmp/depth_chars_35_v5.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

OFFSETS = {
    'Gate_3b2fa3':           0x3b2fa3,
    'DepthCache_C2_ctor':    0x3d8780,
    'StereoAPI_C1':          0x3f46d0,
    'StereoAPI_C2':          0x3f2c40,
    'StereoAPI_camloop_lo':  0x3f30a0,
    'Triangulator_refine3d': 0x20ca00,
    'SM_229d80': 0x229d80, 'SM_229e30': 0x229e30,
    'SM_22a040': 0x22a040, 'SM_22a910': 0x22a910,
    'SM_22aa50': 0x22aa50, 'SM_22add0': 0x22add0,
    'SM_22aee0': 0x22aee0,
}

BASELINE_28MM = {
    'Gate_3b2fa3': 1, 'DepthCache_C2_ctor': 1,
    'StereoAPI_C1': 1, 'StereoAPI_C2': 1,
    'StereoAPI_camloop_lo': '?',
    'Triangulator_refine3d': 10,
}

_hits = collections.Counter()
_cam_loop_ids = []
_tri_rdis     = set()
_gate_byte0   = None
_gate_rdi_val = None


def read_u8(process, addr):
    if not addr: return None
    err = lldb.SBError()
    d = process.ReadMemory(addr, 1, err)
    return d[0] if err.Success() and len(d) == 1 else None

def read_u32(process, addr):
    if not addr: return None
    err = lldb.SBError()
    d = process.ReadMemory(addr, 4, err)
    return struct.unpack('<I', d)[0] if err.Success() and len(d) == 4 else None

def get_reg(frame, name):
    r = frame.FindRegister(name)
    return r.GetValueAsUnsigned() if r.IsValid() else 0


def handle_bp(process, thread, name):
    global _gate_byte0, _gate_rdi_val
    frame = thread.GetFrameAtIndex(0)
    _hits[name] += 1
    if not frame.IsValid(): return
    if name == 'Gate_3b2fa3':
        rdi = get_reg(frame, 'rdi')
        _gate_rdi_val = rdi
        if _gate_byte0 is None:
            _gate_byte0 = read_u8(process, rdi) if rdi else None
    elif name == 'StereoAPI_camloop_lo':
        r12 = get_reg(frame, 'r12')
        cam_id = read_u32(process, r12) if r12 else None
        _cam_loop_ids.append(cam_id)
    elif name == 'Triangulator_refine3d':
        rdi = get_reg(frame, 'rdi')
        _tri_rdis.add(rdi)


def _find_libcp(target):
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fname = m.GetFileSpec().GetFilename()
        if fname and 'libcp' in fname:
            addr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if addr != lldb.LLDB_INVALID_ADDRESS:
                return addr
    return None


def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)  # async mode: Continue() non-blocking

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print("ERROR: invalid target"); sys.exit(1)

    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    listener = debugger.GetListener()
    err = lldb.SBError()
    process = target.Launch(launch_info, err)
    if not err.Success() or not process.IsValid():
        print(f"ERROR: {err}"); sys.exit(1)

    print(f"PID={process.GetProcessID()}")

    # Wait for entry stop (stop-at-entry)
    event = lldb.SBEvent()
    entry_stopped = False
    deadline = time.time() + 30
    while time.time() < deadline:
        if listener.WaitForEvent(1, event):
            st = lldb.SBProcess.GetStateFromEvent(event)
            print(f"  Entry event: {debugger.StateAsCString(st)}")
            if st == lldb.eStateStopped:
                entry_stopped = True
                break
            elif st in (lldb.eStateExited, lldb.eStateCrashed):
                print(f"  Process ended at entry"); sys.exit(1)

    if not entry_stopped:
        print("Did not get entry stop event")

    # Check if libcp is already loaded
    libcp_base = _find_libcp(target)
    print(f"libcp at entry: {hex(libcp_base) if libcp_base else 'NOT FOUND'}")

    if libcp_base is None:
        # Need to step past dyld init WITHOUT running freely
        # Use a module-load callback or step through init
        # Strategy: single-step with timeout until libcp appears
        print("Stepping until libcp loads...")
        step_deadline = time.time() + 10
        step_count = 0
        while time.time() < step_deadline:
            thread = process.GetSelectedThread()
            thread.StepInstruction(False)  # step over
            # Check for events
            while listener.WaitForEvent(0, event):
                st = lldb.SBProcess.GetStateFromEvent(event)
                if st in (lldb.eStateExited, lldb.eStateCrashed):
                    print(f"  Terminated during step")
                    sys.exit(1)
            libcp_base = _find_libcp(target)
            step_count += 1
            if libcp_base:
                print(f"  libcp found after {step_count} steps: 0x{libcp_base:016x}")
                break

    if libcp_base is None:
        # Last resort: try continuing with a short time window and very frequent polling
        print("Step failed; trying 0.1s micro-continue...")
        for _ in range(10):
            process.Continue()
            time.sleep(0.1)
            process.Stop()
            # Drain events
            while listener.WaitForEvent(0, event): pass
            libcp_base = _find_libcp(target)
            if libcp_base: break

    if libcp_base is None:
        print("ERROR: libcp not found"); process.Kill(); sys.exit(1)

    print(f"libcp base confirmed: 0x{libcp_base:016x}")

    # Set ALL BPs now (before any free run)
    bp_id_to_name = {}
    for name, offset in OFFSETS.items():
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} invalid"); continue
        bp_id_to_name[bp.GetID()] = name
        print(f"  BP[{bp.GetID()}] {name} @ libcp+0x{offset:x}")

    print(f"\nAll BPs armed. Starting event loop...")
    process.Continue()

    start_time = time.time()
    MAX_TIME = 300
    last_tri_hit = None
    TRI_SETTLE = 15  # seconds after last Tri hit

    while time.time() - start_time < MAX_TIME:
        got_event = listener.WaitForEvent(2, event)

        if not got_event:
            # No event in 2s — check if depth is done
            if last_tri_hit and (time.time() - last_tri_hit) > TRI_SETTLE:
                print(f"\nTri settled ({TRI_SETTLE}s no new hits). Depth done.")
                break
            continue

        state = lldb.SBProcess.GetStateFromEvent(event)

        if state == lldb.eStateExited:
            print(f"\nProcess exited code={process.GetExitStatus()}")
            break

        if state == lldb.eStateCrashed:
            print(f"\nProcess crashed")
            break

        if state == lldb.eStateStopped:
            found_any_bp = False
            for tidx in range(process.GetNumThreads()):
                thread = process.GetThreadAtIndex(tidx)
                if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
                    bp_id = thread.GetStopReasonDataAtIndex(0)
                    name  = bp_id_to_name.get(bp_id)
                    if name:
                        handle_bp(process, thread, name)
                        found_any_bp = True
                        if name == 'Triangulator_refine3d':
                            last_tri_hit = time.time()

            elapsed = time.time() - start_time
            sm_sum = sum(_hits.get(f'SM_{x}',0) for x in
                         ['229d80','229e30','22a040','22a910','22aa50','22add0','22aee0'])
            if found_any_bp:
                print(f"  [{elapsed:.1f}s] Gate={_hits['Gate_3b2fa3']} "
                      f"SAC1={_hits['StereoAPI_C1']} SAC2={_hits['StereoAPI_C2']} "
                      f"DC={_hits['DepthCache_C2_ctor']} Tri={_hits['Triangulator_refine3d']} "
                      f"CAM={_hits['StereoAPI_camloop_lo']} SM={sm_sum}")
            process.Continue()

    if (time.time() - start_time) >= MAX_TIME:
        print(f"\nTimeout {MAX_TIME}s")

    if process.GetState() not in (lldb.eStateExited, lldb.eStateDetached):
        process.Kill()
        deadline2 = time.time() + 5
        while time.time() < deadline2:
            if listener.WaitForEvent(1, event):
                if lldb.SBProcess.GetStateFromEvent(event) in (lldb.eStateExited,):
                    break

    print_summary()
    try: debugger.Destroy()
    except Exception: pass


def print_summary():
    print("\n" + "=" * 72)
    print("35mm DEPTH PIPELINE — v5 — profile=3")
    print(f"LRI: {LRI_PATH}")
    print("=" * 72)

    rows = [
        ('--- DEPTH PIPELINE ---', None),
        ('Gate (0x3b2fa3)',                  'Gate_3b2fa3'),
        ('DepthCache C2 ctor (0x3d8780)',    'DepthCache_C2_ctor'),
        ('StereoAsyncAPI C1 (0x3f46d0)',     'StereoAPI_C1'),
        ('StereoAsyncAPI C2 (0x3f2c40)',     'StereoAPI_C2'),
        ('StereoAPI camloop lo (0x3f30a0)',  'StereoAPI_camloop_lo'),
        ('Triangulator refine3dPoints',      'Triangulator_refine3d'),
        ('--- STATE MACHINE ---', None),
        ('SM 0x229d80', 'SM_229d80'), ('SM 0x229e30', 'SM_229e30'),
        ('SM 0x22a040', 'SM_22a040'), ('SM 0x22a910', 'SM_22a910'),
        ('SM 0x22aa50', 'SM_22aa50'), ('SM 0x22add0', 'SM_22add0'),
        ('SM 0x22aee0', 'SM_22aee0'),
    ]

    print(f"  {'Probe point':<42} {'35mm hits':>9}  {'28mm base':>9}")
    print("  " + "-" * 65)
    for label, key in rows:
        if key is None:
            print(f"\n  {label}"); continue
        h35 = _hits[key]
        b28 = BASELINE_28MM.get(key, '?')
        delta = f"  ({h35 - b28:+d})" if isinstance(b28, int) else ''
        print(f"  {label:<42} {h35:>9}  {str(b28):>9}{delta}")

    if _gate_byte0 is not None:
        print(f"\n  Gate rdi=0x{_gate_rdi_val:016x}, [rdi+0]=0x{_gate_byte0:02x}")
    else:
        print(f"\n  Gate: NOT CAPTURED")

    if _cam_loop_ids:
        distinct = sorted(set(x for x in _cam_loop_ids if x is not None and 0 <= x <= 20))
        print(f"  StereoAsyncAPI cam-list: {_cam_loop_ids}  distinct={distinct}")
    else:
        print(f"  StereoAsyncAPI cam-list: NO HITS")

    if _tri_rdis:
        print(f"  Triangulator self* ptrs: {[hex(x) for x in sorted(_tri_rdis)]}")

    sm_active = [k for k in ['SM_229d80','SM_229e30','SM_22a040','SM_22a910',
                              'SM_22aa50','SM_22add0','SM_22aee0'] if _hits[k] > 0]
    print(f"  Active SM handlers: {sm_active}")
    print("\n" + "=" * 72)
    print("END OF REPORT")
    print("=" * 72)


if __name__ == '__main__':
    main()
