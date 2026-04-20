"""
BP at the CCM tree-walker functions:
  - 0x3f6200 : the throwing tree walker (called via dispatcher 0x3f6170 with edx=cam_id)
  - 0x3f6940 : the alternate (cross-class) tree walker (called via dispatcher with edx=cam_id)
  - 0x3f6170 : the dispatcher itself - capture edx (original cam_id) on entry

Capture distinct cam_id (edx) values to determine which cam_ids actually drive the CCM lookup.
A2 = cam_id 1.
"""

import lldb

walker_2200_calls = {}     # cam_id -> count
walker_6940_calls = {}     # cam_id -> count
dispatcher_calls = {}      # cam_id -> count
hit_total = [0]


def disp_callback(frame, bp_loc, _):
    """0x3f6170 dispatcher entry. edx = original cam_id."""
    edx = frame.FindRegister('rdx').GetValueAsUnsigned() & 0xffffffff
    dispatcher_calls[edx] = dispatcher_calls.get(edx, 0) + 1
    hit_total[0] += 1
    return False


def walker_2200_callback(frame, bp_loc, _):
    """0x3f6200 throwing tree-walker entry. edx = cam_id key."""
    edx = frame.FindRegister('rdx').GetValueAsUnsigned() & 0xffffffff
    walker_2200_calls[edx] = walker_2200_calls.get(edx, 0) + 1
    return False


def walker_6940_callback(frame, bp_loc, _):
    """0x3f6940 alternate tree-walker entry. edx = cam_id key."""
    edx = frame.FindRegister('rdx').GetValueAsUnsigned() & 0xffffffff
    walker_6940_calls[edx] = walker_6940_calls.get(edx, 0) + 1
    return False
