import builtins
import struct


def reset():
    builtins.l16_refined_tuple_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def hit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    x_data = _read(process, rbp - 0x4310, 4)
    y_data = _read(process, rbp - 0x4320, 4)
    begin_data = _read(process, rbp - 0x1800, 8)
    end_data = _read(process, rbp - 0x17F8, 8)
    rec_off_data = _read(process, rbp - 0x4300, 8)
    if None in (x_data, y_data, begin_data, end_data, rec_off_data):
        builtins.l16_refined_tuple_first = {"error": "failed to read stack packet"}
        return

    begin = _u64(begin_data)
    end = _u64(end_data)
    record_offset = _u64(rec_off_data)
    record = begin + record_offset
    rax = _u(frame, "rax")
    rcx = _u(frame, "rcx")
    out_addr = rcx + rax * 4
    diff = end - begin if end >= begin else None
    builtins.l16_refined_tuple_first = {
        "rbp": rbp,
        "begin": begin,
        "end": end,
        "diff": diff,
        "npartners": diff // 0x280 if diff is not None else None,
        "record_offset": record_offset,
        "record": record,
        "x_stack_float": _f32(x_data),
        "y_stack_float": _f32(y_data),
        "out_base": rcx,
        "out_index_times_3": rax,
        "out_addr_first_float": out_addr,
    }


def report(label):
    if not hasattr(builtins, "l16_refined_tuple_first"):
        reset()
    print("L16_REFINED_TUPLE_PROBE_BEGIN", label)
    print("refined_tuple", builtins.l16_refined_tuple_first)
    print("L16_REFINED_TUPLE_PROBE_END", label)
