#!/usr/bin/env python3
"""
profile=2 (CAMERA) characterization probe at 28mm L16_02130.lri

Run: arch -x86_64 /usr/bin/python3 probe_profile2_28mm.py

Uses LLDB Python bindings. SetScriptCallbackFunction requires functions
registered in '__main__' module (LLDB looks them up there by name string).
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

LRI_PATH      = '/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri'
OUT_PATH      = '/tmp/p2_28mm_probe.hdr'
LRI_PROCESS   = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process'
LIBCP_DIR     = '/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks'

# libcp-relative offsets (from phoenix-truth-2026-04-17.md + probe brief)
OFFSETS = {
    'IRAMP_body':            0x3661b0,
    'SIC_init':              0x3e0330,
    'DepthCache_ctor':       0x3eaf00,
    'StereoAsyncAPI_C1':     0x3f46d0,
    'StereoAsyncAPI_C2':     0x3f2c40,
    'Triangulator_refine3d': 0x20ca00,
    'CCMInterp':             0x350bc0,
    'IRAMP_dispatcher':      0x3f6170,
}

# Profile=3 baseline (from truth doc + Q10 28mm report)
P3_BASELINE = {
    'IRAMP_body':            300,
    'SIC_init':              5,       # B1-B5 (cam_ids 5,6,7,8,9)
    'DepthCache_ctor':       0,       # 0 on bridge (GUI-only per §6)
    'StereoAsyncAPI_C1':     0,       # 0 on bridge
    'StereoAsyncAPI_C2':     0,
    'Triangulator_refine3d': 0,       # 0 on bridge
    'CCMInterp':             12,      # 12 hits, 3 dest buffers, 5 cam inputs
    'IRAMP_dispatcher':      '?',
}

# ---- shared mutable state (module-level so callbacks can mutate) ----
_hits = collections.Counter()
_sic_cam_rdi = []   # cam_id read from [rdi+0x60] at SIC_init
_sic_cam_rsi = []   # cam_id read from [rsi+0x60] at SIC_init
_disp_rsi_raw = []  # raw rsi value at IRAMP_dispatcher (likely cam_id int)
_disp_rdi_cam = []  # [rdi+0x60] at IRAMP_dispatcher
_ccm_regs = []      # (rdi_val, rsi_val) at CCMInterp
_process_ref = [None]  # filled in main() for callbacks to read memory


def _read_u32(addr):
    proc = _process_ref[0]
    if proc is None or addr == 0:
        return None
    err = lldb.SBError()
    data = proc.ReadMemory(addr, 4, err)
    if err.Success() and len(data) == 4:
        return struct.unpack('<I', data)[0]
    return None


# ---- callback functions (referenced by name via SetScriptCallbackFunction) ----
# Signature: (frame, bp_loc, extra_args, internal_dict) -> bool (False = don't stop)

def cb_iramp_body(frame, bp_loc, extra_args, internal_dict):
    _hits['IRAMP_body'] += 1
    return False

def cb_sic_init(frame, bp_loc, extra_args, internal_dict):
    _hits['SIC_init'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    rsi = frame.FindRegister('rsi').GetValueAsUnsigned()
    _sic_cam_rdi.append(_read_u32(rdi + 0x60) if rdi else None)
    _sic_cam_rsi.append(_read_u32(rsi + 0x60) if rsi else None)
    return False

def cb_depthcache(frame, bp_loc, extra_args, internal_dict):
    _hits['DepthCache_ctor'] += 1
    return False

def cb_stereo_c1(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAsyncAPI_C1'] += 1
    return False

def cb_stereo_c2(frame, bp_loc, extra_args, internal_dict):
    _hits['StereoAsyncAPI_C2'] += 1
    return False

def cb_triangulator(frame, bp_loc, extra_args, internal_dict):
    _hits['Triangulator_refine3d'] += 1
    return False

def cb_ccm(frame, bp_loc, extra_args, internal_dict):
    _hits['CCMInterp'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    rsi = frame.FindRegister('rsi').GetValueAsUnsigned()
    _ccm_regs.append((rdi, rsi))
    return False

def cb_dispatcher(frame, bp_loc, extra_args, internal_dict):
    _hits['IRAMP_dispatcher'] += 1
    rdi = frame.FindRegister('rdi').GetValueAsUnsigned()
    rsi = frame.FindRegister('rsi').GetValueAsUnsigned()
    _disp_rsi_raw.append(rsi)  # likely cam_id integer
    _disp_rdi_cam.append(_read_u32(rdi + 0x60) if rdi else None)
    return False


# Map name -> (callback_fn_name, callback_fn)
BP_CONFIG = [
    ('IRAMP_body',            'cb_iramp_body'),
    ('SIC_init',              'cb_sic_init'),
    ('DepthCache_ctor',       'cb_depthcache'),
    ('StereoAsyncAPI_C1',     'cb_stereo_c1'),
    ('StereoAsyncAPI_C2',     'cb_stereo_c2'),
    ('Triangulator_refine3d', 'cb_triangulator'),
    ('CCMInterp',             'cb_ccm'),
    ('IRAMP_dispatcher',      'cb_dispatcher'),
]


def main():
    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(True)

    target = debugger.CreateTargetWithFileAndArch(LRI_PROCESS, 'x86_64')
    if not target.IsValid():
        print(f"ERROR: Could not create target from {LRI_PROCESS}")
        sys.exit(1)

    # Build launch info — no stop-at-entry; find libcp after brief sleep
    launch_info = lldb.SBLaunchInfo([LRI_PATH, OUT_PATH, '--profile', '2'])
    env = lldb.SBEnvironment()
    env.Set('DYLD_LIBRARY_PATH', LIBCP_DIR, True)
    launch_info.SetEnvironment(env, True)
    launch_info.SetWorkingDirectory('/Users/ryaker/Dev/L16_Lumen_ReverseEngineering')
    # Don't stop at entry — let it load libraries, then we'll find libcp
    # But we need to set BPs before IRAMP fires, so use stop-at-entry
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    error = lldb.SBError()
    process = target.Launch(launch_info, error)
    if not error.Success() or not process.IsValid():
        print(f"ERROR launching: {error}")
        sys.exit(1)

    print(f"Process launched PID={process.GetProcessID()}")

    # Wait for stop at entry
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

    # libcp may not be loaded yet at entry; continue briefly then stop
    # Actually on macOS with dyld, all libs load before main() on stop-at-entry
    libcp_base = _find_libcp(target)
    if libcp_base is None:
        print("  libcp not visible at entry stop. Continuing briefly...")
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

    # Set breakpoints using SetScriptCallbackFunction
    # LLDB looks up function names in __main__ module
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
            print(f"  BP {name} @ 0x{addr:x} (libcp+0x{offset:x})")

    print(f"\nAll BPs set. Running profile=2 render (profile=3 took ~300 IRAMP iterations)...")
    start_time = time.time()
    process.Continue()

    # Poll for completion
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
            print(f"  [{elapsed:.0f}s elapsed; IRAMP_body={_hits['IRAMP_body']} SIC={_hits['SIC_init']}]")
            last_report = time.time()
        time.sleep(0.5)
    else:
        print(f"\nTIMEOUT after {timeout}s")
        process.Kill()

    print_summary()
    debugger.Destroy()


def _find_libcp(target):
    for i in range(target.GetNumModules()):
        m = target.GetModuleAtIndex(i)
        fname = m.GetFileSpec().GetFilename()
        if fname and 'libcp' in fname:
            addr = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if addr != lldb.LLDB_INVALID_ADDRESS:
                return addr
    return None


def print_summary():
    print("\n" + "="*72)
    print("PROFILE=2 (CAMERA) vs PROFILE=3 (DESKTOP) @ 28mm L16_02130")
    print("="*72)
    print(f"{'Probe point':<35} {'p=2 hits':>10}  {'p=3 baseline':>14}")
    print("-"*72)
    rows = [
        ('IRAMP_body (0x3661b0)',            'IRAMP_body'),
        ('SIC_init (0x3e0330)',              'SIC_init'),
        ('DepthCache_ctor (0x3eaf00)',       'DepthCache_ctor'),
        ('StereoAsyncAPI_C1 (0x3f46d0)',     'StereoAsyncAPI_C1'),
        ('StereoAsyncAPI_C2 (0x3f2c40)',     'StereoAsyncAPI_C2'),
        ('Triangulator_refine3d (0x20ca00)', 'Triangulator_refine3d'),
        ('CCMInterp (0x350bc0)',             'CCMInterp'),
        ('IRAMP_dispatcher (0x3f6170)',      'IRAMP_dispatcher'),
    ]
    for label, key in rows:
        p2 = _hits[key]
        p3 = P3_BASELINE.get(key, '?')
        delta = ''
        if isinstance(p3, int):
            delta = f"  ({p2-p3:+d})"
        print(f"  {label:<33} {p2:>10}  {str(p3):>14}{delta}")

    print()
    # SIC cam_ids
    valid_rdi = [x for x in _sic_cam_rdi if x is not None and 0 <= x <= 15]
    valid_rsi = [x for x in _sic_cam_rsi if x is not None and 0 <= x <= 15]
    print(f"SIC_init cam_ids [rdi+0x60] raw: {_sic_cam_rdi}")
    print(f"SIC_init cam_ids [rsi+0x60] raw: {_sic_cam_rsi}")
    print(f"  unique valid [rdi+0x60]: {sorted(set(valid_rdi))}")
    print(f"  unique valid [rsi+0x60]: {sorted(set(valid_rsi))}")
    print()

    # Dispatcher cam_ids
    valid_disp_rsi = [x for x in _disp_rsi_raw if 0 <= x <= 15]
    valid_disp_rdi = [x for x in _disp_rdi_cam if x is not None and 0 <= x <= 15]
    print(f"IRAMP_dispatcher rsi raw (cam_id?): {_disp_rsi_raw}")
    print(f"IRAMP_dispatcher [rdi+0x60]:         {_disp_rdi_cam}")
    print(f"  unique rsi in [0,15]: {sorted(set(valid_disp_rsi))}")
    print(f"  unique [rdi+0x60] in [0,15]: {sorted(set(valid_disp_rdi))}")
    print()

    # CCMInterp
    print(f"CCMInterp total calls: {len(_ccm_regs)}")
    if _ccm_regs:
        unique_rdi = sorted(set(r for r, _ in _ccm_regs))
        unique_rsi = sorted(set(r for _, r in _ccm_regs))
        print(f"  Unique rdi (dest buf ptrs): {len(unique_rdi)} → {[hex(x) for x in unique_rdi[:8]]}")
        print(f"  Unique rsi (src/cam ptrs):  {len(unique_rsi)} → {[hex(x) for x in unique_rsi[:8]]}")

    print()
    if os.path.exists(OUT_PATH):
        sz = os.path.getsize(OUT_PATH)
        print(f"Output: {OUT_PATH} ({sz:,} bytes = {sz/1e6:.1f} MB)")
    else:
        print(f"Output NOT found: {OUT_PATH}")
    print("="*72)


if __name__ == '__main__':
    main()
