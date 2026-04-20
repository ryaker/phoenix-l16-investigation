#!/usr/bin/env python3
"""
35mm depth pipeline characterization probe — profile=3.

Probes:
  1. StereoAsyncAPI C2 (0x3f2c40) cam-list loop (0x3f30a0..0x3f3145) — cam_idx capture
  2. Triangulator::refine3dPoints (0x20ca00) hit count
  3. State machine handlers (0x229d80, 0x229e30, 0x22a040, 0x22a910, 0x22aa50, 0x22add0, 0x22aee0)
  4. DepthCache C2 ctor (0x3d8780), StereoAsyncAPI C1 (0x3f46d0), C2 (0x3f2c40)
  5. Gate (0x3b2fa3)
  6. IRAMP body (0x3661b0) — tile count at 35mm vs 28mm
  7. SIC init (0x3e0330) — cam_ids
  8. IRAMP dispatcher (0x3f6170) — cam_ids

Run: arch -x86_64 /usr/bin/python3 probe_depth_35mm.py

NOTE: cam_idx inside StereoAsyncAPI cam-list loop read from [rdi+0x60] or via
      the cam_id getter at libcp+0xf2720 ([rdi+0x60]).
"""

import sys
import os
import struct
import time
import collections

LLDB_PYTHON = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python'
if LLDB_PYTHON not in sys.path:
    sys.path.insert(0, LLDB_PYTHON)

import lldb

LRI_PATH    = '/Volumes/Base Photos/Light/2018-10-25/L16_02951.lri'
OUT_PATH    = '/tmp/depth_chars_35.hdr'
LRI_PROCESS = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

# libcp-relative VAs from D7 + spawn prompt
OFFSETS = {
    # Depth core
    'DepthCache_C2_ctor':   0x3d8780,    # C2 body (C1 thunk 0x3d8b70)
    'StereoAPI_C1':         0x3f46d0,
    'StereoAPI_C2':         0x3f2c40,
    'Triangulator_refine3d':0x20ca00,
    # StereoAsyncAPI cam-list loop boundaries
    'StereoAPI_camloop_lo': 0x3f30a0,    # loop entry
    'StereoAPI_camloop_hi': 0x3f3145,    # loop exit
    # State machine handlers
    'SM_229d80':            0x229d80,
    'SM_229e30':            0x229e30,
    'SM_22a040':            0x22a040,
    'SM_22a910':            0x22a910,
    'SM_22aa50':            0x22aa50,
    'SM_22add0':            0x22add0,
    'SM_22aee0':            0x22aee0,
    # Gate
    'Gate_3b2fa3':          0x3b2fa3,
    # Color-path reference points (compare vs 28mm)
    'IRAMP_body':           0x3661b0,
    'SIC_init':             0x3e0330,
    'IRAMP_dispatcher':     0x3f6170,
}

# 28mm profile=3 baselines from phoenix-truth-2026-04-17.md + depth_unlock_verification.md
BASELINE_28MM = {
    'DepthCache_C2_ctor':   1,
    'StereoAPI_C1':         1,
    'StereoAPI_C2':         1,
    'Triangulator_refine3d':10,
    'StereoAPI_camloop_lo': '?',
    'StereoAPI_camloop_hi': '?',
    'SM_229d80':            '?',
    'SM_229e30':            '?',
    'SM_22a040':            '?',
    'SM_22a910':            '?',
    'SM_22aa50':            '?',
    'SM_22add0':            '?',
    'SM_22aee0':            '?',
    'Gate_3b2fa3':          1,
    'IRAMP_body':           300,
    'SIC_init':             5,
    'IRAMP_dispatcher':     7,
}

# Mutable state
_hits = collections.Counter()
_cam_loop_rdis  = []   # rdi vals at cam-list loop entry (pointer to cam struct)
_cam_loop_ids   = []   # [rdi+0x60] uint32 cam_ids seen inside cam-list loop
_triangulator_rdis = []  # rdi at each Triangulator refine3dPoints call
_dispatcher_cam_ids = []  # [rdi+0x60] at IRAMP dispatcher
_sic_cam_ids   = []    # [rdi+0x60] at SIC init
_gate_rdi_vals = []    # rdi at gate (imageStorageObj)
_gate_byte0    = []    # [rdi+0x00] at gate
_sm_tids       = []    # (handler_name, thread_id) to track concurrency
_process_ref   = [None]


def _read_u32(addr):
    proc = _process_ref[0]
    if proc is None or addr == 0:
        return None
    err = lldb.SBError()
    data = proc.ReadMemory(addr, 4, err)
    if err.Success() and len(data) == 4:
        return struct.unpack('<I', data)[0]
    return None

def _read_u8(addr):
    proc = _process_ref[0]
    if proc is None or addr == 0:
        return None
    err = lldb.SBError()
    data = proc.ReadMemory(addr, 1, err)
    if err.Success() and len(data) == 1:
        return data[0]
    return None


# ---- Callbacks ----

def cb_depthcache_c2(frame, bp_loc, extra_args, internal_dict):
    _hits['DepthCache_C2_ctor'] += 1
    return False

def cb_stereo_c1(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAPI_C1'] += 1
    return False

def cb_stereo_c2(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAPI_C2'] += 1
    return False

def cb_triangulator(frame, bp_loc, extra_args, internal_dict):
    _hits['Triangulator_refine3d'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    _triangulator_rdis.append(rdi)
    return False

def cb_camloop_lo(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAPI_camloop_lo'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    _cam_loop_rdis.append(rdi)
    cam_id = _read_u32(rdi + 0x60) if rdi else None
    _cam_loop_ids.append(cam_id)
    return False

def cb_camloop_hi(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAPI_camloop_hi'] += 1
    return False

def cb_sm_229d80(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_229d80'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_229d80', tid))
    return False

def cb_sm_229e30(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_229e30'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_229e30', tid))
    return False

def cb_sm_22a040(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_22a040'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_22a040', tid))
    return False

def cb_sm_22a910(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_22a910'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_22a910', tid))
    return False

def cb_sm_22aa50(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_22aa50'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_22aa50', tid))
    return False

def cb_sm_22add0(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_22add0'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_22add0', tid))
    return False

def cb_sm_22aee0(frame, bp_loc, extra_args, internal_dict):
    _hits['SM_22aee0'] += 1
    tid = frame.GetThread().GetThreadID()
    _sm_tids.append(('SM_22aee0', tid))
    return False

def cb_gate(frame, bp_loc, extra_args, internal_dict):
    _hits['Gate_3b2fa3'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    _gate_rdi_vals.append(rdi)
    b0 = _read_u8(rdi) if rdi else None
    _gate_byte0.append(b0)
    return False

def cb_iramp_body(frame, bp_loc, extra_args, internal_dict):
    _hits['IRAMP_body'] += 1
    return False

def cb_sic_init(frame, bp_loc, extra_args, internal_dict):
    _hits['SIC_init'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    cam_id = _read_u32(rdi + 0x60) if rdi else None
    _sic_cam_ids.append(cam_id)
    return False

def cb_iramp_dispatcher(frame, bp_loc, extra_args, internal_dict):
    _hits['IRAMP_dispatcher'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    cam_id = _read_u32(rdi + 0x60) if rdi else None
    _dispatcher_cam_ids.append(cam_id)
    return False


BP_CONFIG = [
    ('DepthCache_C2_ctor',    'cb_depthcache_c2'),
    ('StereoAPI_C1',          'cb_stereo_c1'),
    ('StereoAPI_C2',          'cb_stereo_c2'),
    ('Triangulator_refine3d', 'cb_triangulator'),
    ('StereoAPI_camloop_lo',  'cb_camloop_lo'),
    ('StereoAPI_camloop_hi',  'cb_camloop_hi'),
    ('SM_229d80',             'cb_sm_229d80'),
    ('SM_229e30',             'cb_sm_229e30'),
    ('SM_22a040',             'cb_sm_22a040'),
    ('SM_22a910',             'cb_sm_22a910'),
    ('SM_22aa50',             'cb_sm_22aa50'),
    ('SM_22add0',             'cb_sm_22add0'),
    ('SM_22aee0',             'cb_sm_22aee0'),
    ('Gate_3b2fa3',           'cb_gate'),
    ('IRAMP_body',            'cb_iramp_body'),
    ('SIC_init',              'cb_sic_init'),
    ('IRAMP_dispatcher',      'cb_iramp_dispatcher'),
]


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
    debugger.SetAsync(True)

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print(f"ERROR: Could not create target from {LRI_PROCESS}")
        sys.exit(1)

    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    error = lldb.SBError()
    process = target.Launch(launch_info, error)
    if not error.Success() or not process.IsValid():
        print(f"ERROR launching: {error}")
        sys.exit(1)

    print(f"Process PID={process.GetProcessID()}")

    deadline = time.time() + 30
    while time.time() < deadline:
        if process.GetState() == lldb.eStateStopped:
            break
        time.sleep(0.2)
    else:
        print("ERROR: did not stop at entry")
        process.Kill()
        sys.exit(1)

    print("Stopped at entry. Finding libcp...")
    libcp_base = _find_libcp(target)
    if libcp_base is None:
        process.Continue()
        time.sleep(3)
        process.Stop()
        time.sleep(1)
        libcp_base = _find_libcp(target)

    if libcp_base is None:
        print("ERROR: libcp not found")
        process.Kill()
        sys.exit(1)

    print(f"libcp base: 0x{libcp_base:016x}")
    _process_ref[0] = process

    for name, fn_name in BP_CONFIG:
        offset = OFFSETS[name]
        addr = libcp_base + offset
        bp = target.BreakpointCreateByAddress(addr)
        if not bp.IsValid():
            print(f"  WARNING: BP {name} @ 0x{addr:x} invalid")
            continue
        err = bp.SetScriptCallbackFunction(fn_name)
        if hasattr(err, 'Fail') and err.Fail():
            print(f"  WARNING: SetScriptCallbackFunction failed for {name}: {err}")
        else:
            print(f"  BP {name} @ libcp+0x{offset:x}")

    print(f"\nRunning 35mm profile=3 render...")
    start_time = time.time()
    process.Continue()

    timeout = 600
    deadline = time.time() + timeout
    last_report = time.time()

    while time.time() < deadline:
        state = process.GetState()
        if state == lldb.eStateExited:
            elapsed = time.time() - start_time
            print(f"\nProcess exited. Code={process.GetExitStatus()}, elapsed={elapsed:.1f}s")
            break
        if state == lldb.eStateCrashed:
            elapsed = time.time() - start_time
            print(f"\nProcess CRASHED after {elapsed:.1f}s")
            break
        if state == lldb.eStateStopped:
            elapsed = time.time() - start_time
            thread = process.GetSelectedThread()
            reason = thread.GetStopReason()
            print(f"  [stopped at {elapsed:.1f}s reason={reason}, continuing]")
            process.Continue()
        if time.time() - last_report > 30:
            elapsed = time.time() - start_time
            print(f"  [{elapsed:.0f}s] IRAMP={_hits['IRAMP_body']} Tri={_hits['Triangulator_refine3d']} SM=({_hits['SM_229d80']},{_hits['SM_229e30']},{_hits['SM_22a040']},...)")
            last_report = time.time()
        time.sleep(0.5)
    else:
        print(f"\nTIMEOUT after {timeout}s")
        process.Kill()

    print_summary()
    debugger.Destroy()


def print_summary():
    print("\n" + "=" * 76)
    print("35mm DEPTH PIPELINE CHARACTERIZATION — profile=3")
    print("LRI: /Volumes/Base Photos/Light/2018-10-25/L16_02951.lri")
    print("=" * 76)

    rows = [
        ('--- DEPTH PIPELINE ---', None),
        ('Gate (0x3b2fa3)',              'Gate_3b2fa3'),
        ('DepthCache C2 ctor (0x3d8780)','DepthCache_C2_ctor'),
        ('StereoAsyncAPI C1 (0x3f46d0)', 'StereoAPI_C1'),
        ('StereoAsyncAPI C2 (0x3f2c40)', 'StereoAPI_C2'),
        ('StereoAPI camloop lo (0x3f30a0)','StereoAPI_camloop_lo'),
        ('StereoAPI camloop hi (0x3f3145)','StereoAPI_camloop_hi'),
        ('Triangulator::refine3dPoints', 'Triangulator_refine3d'),
        ('--- STATE MACHINE ---', None),
        ('SM 0x229d80',                 'SM_229d80'),
        ('SM 0x229e30',                 'SM_229e30'),
        ('SM 0x22a040',                 'SM_22a040'),
        ('SM 0x22a910',                 'SM_22a910'),
        ('SM 0x22aa50',                 'SM_22aa50'),
        ('SM 0x22add0',                 'SM_22add0'),
        ('SM 0x22aee0',                 'SM_22aee0'),
        ('--- COLOR PATH (compare) ---', None),
        ('IRAMP body (0x3661b0)',        'IRAMP_body'),
        ('SIC init (0x3e0330)',          'SIC_init'),
        ('IRAMP dispatcher (0x3f6170)', 'IRAMP_dispatcher'),
    ]

    print(f"  {'Probe point':<40} {'35mm hits':>10}  {'28mm base':>10}")
    print("  " + "-" * 64)
    for label, key in rows:
        if key is None:
            print(f"\n  {label}")
            continue
        h35 = _hits[key]
        b28 = BASELINE_28MM.get(key, '?')
        delta = ''
        if isinstance(b28, int):
            delta = f"  ({h35 - b28:+d})"
        print(f"  {label:<40} {h35:>10}  {str(b28):>10}{delta}")

    # Gate detail
    if _gate_rdi_vals:
        print(f"\n  Gate rdi=0x{_gate_rdi_vals[0]:016x}, [rdi+0]=0x{_gate_byte0[0]:02x}")

    # Cam-list loop cam_ids (distinct)
    if _cam_loop_ids:
        distinct_cams = sorted(set(x for x in _cam_loop_ids if x is not None))
        print(f"\n  StereoAsyncAPI cam-list loop cam_ids ({len(_cam_loop_ids)} iterations): {_cam_loop_ids}")
        print(f"  Distinct cam_ids in cam-list: {distinct_cams}")

    # Triangulator distinct rdi pointers
    if _triangulator_rdis:
        distinct_rdis = sorted(set(_triangulator_rdis))
        print(f"\n  Triangulator rdi ptrs ({len(_triangulator_rdis)} calls): {[hex(x) for x in distinct_rdis]}")

    # IRAMP dispatcher cam_ids
    if _dispatcher_cam_ids:
        dcams = sorted(set(x for x in _dispatcher_cam_ids if x is not None))
        print(f"\n  IRAMP dispatcher cam_ids ({_hits['IRAMP_dispatcher']} hits): {dcams}")

    # SIC cam_ids
    if _sic_cam_ids:
        scams = sorted(set(x for x in _sic_cam_ids if x is not None))
        print(f"\n  SIC init cam_ids ({_hits['SIC_init']} hits): {scams}")

    # State machine active handlers summary
    sm_active = {h for h, _ in _sm_tids}
    sm_tids_by_handler = collections.Counter(h for h, _ in _sm_tids)
    print(f"\n  State machine active handlers: {sm_active}")
    print(f"  SM hit distribution: {dict(sm_tids_by_handler)}")

    print("\n" + "=" * 76)
    print("END OF REPORT")
    print("=" * 76)


if __name__ == '__main__':
    main()
