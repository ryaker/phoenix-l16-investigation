"""
Shared state module for profile2 LLDB probe.
Imported by breakpoint commands in profile2_probe.lldb.
"""

import collections
import atexit

_hits = collections.Counter()
sic_cam_ids_rdi = []
sic_cam_ids_rsi = []
dispatcher_cam_ids = []
ccm_rdi_vals = []
ccm_rsi_vals = []

def hit(name):
    _hits[name] += 1

def get(name):
    return _hits.get(name, 0)

def print_summary():
    print("\n" + "="*60)
    print("PROFILE=2 (CAMERA) HIT COUNT SUMMARY")
    print("="*60)
    keys = [
        'IRAMP_body', 'SIC_init', 'DepthCache_ctor',
        'StereoAsyncAPI_C1', 'StereoAsyncAPI_C2',
        'Triangulator_refine3d', 'CCMInterp', 'IRAMP_dispatcher'
    ]
    p3_baseline = {
        'IRAMP_body': 300,
        'SIC_init': 5,        # B1-B5 at 28mm
        'DepthCache_ctor': 1,
        'StereoAsyncAPI_C1': 1,
        'StereoAsyncAPI_C2': 0,  # not tracked baseline
        'Triangulator_refine3d': 10,
        'CCMInterp': 12,
        'IRAMP_dispatcher': None,  # not tracked separately in baseline
    }
    print(f"{'Breakpoint':<30} {'p=2 hits':>10}  {'p=3 baseline':>14}")
    print("-"*60)
    for k in keys:
        p3 = p3_baseline.get(k)
        p3_str = str(p3) if p3 is not None else '?'
        print(f"  {k:<28} {_hits.get(k, 0):>10}  {p3_str:>14}")
    print()
    print(f"SIC cam_ids (rdi+0x60): {sic_cam_ids_rdi}")
    print(f"SIC cam_ids (rsi+0x60): {sic_cam_ids_rsi}")
    print(f"Unique SIC rdi cam_ids: {sorted(set(sic_cam_ids_rdi))}")
    print(f"Unique SIC rsi cam_ids: {sorted(set(sic_cam_ids_rsi))}")
    print()
    print(f"Dispatcher cam_ids (rsi): {dispatcher_cam_ids}")
    print(f"Unique dispatcher cam_ids: {sorted(set(dispatcher_cam_ids))}")
    print()
    print(f"CCMInterp rdi vals (first 15): {ccm_rdi_vals[:15]}")
    print(f"CCMInterp rsi vals (first 15): {ccm_rsi_vals[:15]}")
    print("="*60)

atexit.register(print_summary)
