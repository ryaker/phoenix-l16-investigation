#!/usr/bin/env python3
"""
35mm depth probe v3 — async mode with event listener.

Key fix: uses SBListener / WaitForEvent to avoid polling.
Stops ONLY on breakpoint stops, ignores thread creation/destruction stops.
Kills process after collecting depth data (Gate+ctors+camloop+Tri) to avoid
waiting for full IRAMP render.

Run: arch -x86_64 /usr/bin/python3 probe_depth_35mm_v3.py
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
OUT_PATH    = '/tmp/depth_chars_35_v3.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

OFFSETS = {
    'Gate_3b2fa3':           0x3b2fa3,
    'DepthCache_C2_ctor':    0x3d8780,
    'StereoAPI_C1':          0x3f46d0,
    'StereoAPI_C2':          0x3f2c40,
    'StereoAPI_camloop_lo':  0x3f30a0,
    'Triangulator_refine3d': 0x20ca00,
    'SM_229d80':             0x229d80,
    'SM_229e30':             0x229e30,
    'SM_22a040':             0x22a040,
    'SM_22a910':             0x22a910,
    'SM_22aa50':             0x22aa50,
    'SM_22add0':             0x22add0,
    'SM_22aee0':             0x22aee0,
}

BASELINE_28MM = {
    'Gate_3b2fa3': 1, 'DepthCache_C2_ctor': 1,
    'StereoAPI_C1': 1, 'StereoAPI_C2': 1,
    'StereoAPI_camloop_lo': '?',
    'Triangulator_refine3d': 10,
}

_hits = collections.Counter()
_cam_loop_ids   = []
_tri_rdis       = set()
_gate_byte0     = None
_gate_rdi_val   = None


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

    if not frame.IsValid():
        return

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
    debugger.SetAsync(True)   # async mode for event-driven loop

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print("ERROR: invalid target")
        sys.exit(1)

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
        print(f"ERROR launching: {err}")
        sys.exit(1)

    print(f"Launched PID={process.GetProcessID()}")

    # Wait for entry stop
    event = lldb.SBEvent()
    start = time.time()
    found_entry = False
    while time.time() - start < 15:
        if listener.WaitForEvent(1, event):
            if lldb.SBProcess.GetStateFromEvent(event) == lldb.eStateStopped:
                found_entry = True
                break

    if not found_entry:
        print("Did not stop at entry; continuing anyway")

    libcp_base = _find_libcp(target)
    if libcp_base is None:
        print("libcp not loaded at entry; continuing briefly to load dylibs...")
        process.Continue()
        time.sleep(3)
        process.Stop()
        # Drain events
        while listener.WaitForEvent(1, event):
            pass
        libcp_base = _find_libcp(target)

    if libcp_base is None:
        print("ERROR: libcp not found")
        process.Kill()
        sys.exit(1)

    print(f"libcp base: 0x{libcp_base:016x}")

    # Set BPs — in async mode, SetScriptCallbackFunction is problematic;
    # instead we use bp_id_to_name lookup and handle inline.
    bp_id_to_name = {}
    for name, offset in OFFSETS.items():
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} invalid")
            continue
        bp_id_to_name[bp.GetID()] = name
        print(f"  BP[{bp.GetID()}] {name} @ libcp+0x{offset:x}")

    print("\nRunning 35mm depth probe (async event-driven, auto-kill after depth done)...")
    process.Continue()

    MAX_TIME = 300   # 5 min max; depth fires early
    deadline = time.time() + MAX_TIME
    last_report = time.time()

    # Target: capture Gate + ctors + cam-list + Tri data, then continue until Tri settles
    TRI_SETTLE_TIME = 30  # s after last Tri hit before we consider depth done

    last_tri_hit = None
    depth_done = False

    while time.time() < deadline:
        # Wait up to 2s for next event
        if not listener.WaitForEvent(2, event):
            # No event — check if we can declare depth done
            if last_tri_hit is not None and (time.time() - last_tri_hit) > TRI_SETTLE_TIME:
                print(f"\nNo new Tri hits in {TRI_SETTLE_TIME}s — depth computation complete.")
                depth_done = True
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
            # Check all threads for BP hits
            any_bp = False
            for tidx in range(process.GetNumThreads()):
                thread = process.GetThreadAtIndex(tidx)
                if thread.GetStopReason() != lldb.eStopReasonBreakpoint:
                    continue
                any_bp = True
                bp_id = thread.GetStopReasonDataAtIndex(0)
                name  = bp_id_to_name.get(bp_id, f'unknown_{bp_id}')
                handle_bp(process, thread, name)
                if name == 'Triangulator_refine3d':
                    last_tri_hit = time.time()

            # Always continue after stop
            process.Continue()

            if time.time() - last_report > 10:
                elapsed = time.time() - start
                sm_sum = sum(_hits.get(f'SM_{x}', 0) for x in
                             ['229d80','229e30','22a040','22a910','22aa50','22add0','22aee0'])
                print(f"  [{elapsed:.0f}s] Gate={_hits['Gate_3b2fa3']} "
                      f"SAC1={_hits['StereoAPI_C1']} SAC2={_hits['StereoAPI_C2']} "
                      f"DC={_hits['DepthCache_C2_ctor']} "
                      f"Tri={_hits['Triangulator_refine3d']} "
                      f"CAM={_hits['StereoAPI_camloop_lo']} SM={sm_sum}")
                last_report = time.time()

    if not depth_done and (time.time() >= deadline):
        print(f"\nTimeout {MAX_TIME}s")

    # Kill process
    if process.GetState() != lldb.eStateExited:
        print("Killing process...")
        process.Kill()
        while listener.WaitForEvent(2, event):
            if lldb.SBProcess.GetStateFromEvent(event) in (lldb.eStateExited, lldb.eStateDetached):
                break

    print_summary()
    try:
        debugger.Destroy()
    except Exception:
        pass


def print_summary():
    print("\n" + "=" * 72)
    print("35mm DEPTH PIPELINE — v3 — profile=3")
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
            print(f"\n  {label}")
            continue
        h35 = _hits[key]
        b28 = BASELINE_28MM.get(key, '?')
        delta = f"  ({h35 - b28:+d})" if isinstance(b28, int) else ''
        print(f"  {label:<42} {h35:>9}  {str(b28):>9}{delta}")

    if _gate_byte0 is not None:
        print(f"\n  Gate rdi=0x{_gate_rdi_val:016x}, [rdi+0]=0x{_gate_byte0:02x}")
    else:
        print(f"\n  Gate: not captured (fired before BPs armed or never hit)")

    if _cam_loop_ids:
        distinct = sorted(set(x for x in _cam_loop_ids if x is not None and 0 <= x <= 20))
        print(f"  StereoAsyncAPI cam-list: {_cam_loop_ids}  distinct={distinct}")
    else:
        print(f"  StereoAsyncAPI cam-list: no hits captured")

    if _tri_rdis:
        print(f"  Triangulator distinct self* ptrs: {[hex(x) for x in sorted(_tri_rdis)]}")

    sm_active = [k for k in ['SM_229d80','SM_229e30','SM_22a040','SM_22a910',
                              'SM_22aa50','SM_22add0','SM_22aee0'] if _hits[k] > 0]
    print(f"  Active state machine handlers: {sm_active}")

    print("\n" + "=" * 72)
    print("END OF REPORT")
    print("=" * 72)


if __name__ == '__main__':
    main()
