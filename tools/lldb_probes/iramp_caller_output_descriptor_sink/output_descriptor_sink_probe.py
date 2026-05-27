import builtins
import struct


def reset():
    builtins.l16_output_descriptor_sink_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _descriptor(process, addr, first_size):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}

    base = _u64(data, 0x20)
    first = _read(process, base, first_size) if base else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": base,
        "qword_28": _u64(data, 0x28),
        "first_bytes": list(first) if first is not None else None,
        "first_vec4": _f32s(first) if first is not None and first_size == 16 else None,
    }


def hit_after_3e5720(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    r14 = _u(frame, "r14")
    r15 = _u(frame, "r15")
    output_owner_data = _read(process, r14, 8) if r14 else None
    output_owner = _u64(output_owner_data) if output_owner_data else None
    dest_desc = output_owner + 0xF0 if output_owner else None
    temp_desc = rbp - 0x70

    thread = frame.GetThread()
    builtins.l16_output_descriptor_sink_first = {
        "rip": _u(frame, "rip"),
        "thread_id": thread.GetThreadID(),
        "rbp": rbp,
        "r14_output_wrapper": r14,
        "r15_source_context": r15,
        "output_owner_from_wrapper": output_owner,
        "computed_output_descriptor_owner_plus_0xf0": dest_desc,
        "temp_descriptor_rbp_minus_0x70": temp_desc,
        "output_descriptor_after_3e5720": (
            _descriptor(process, dest_desc, 12) if dest_desc else None
        ),
        "temp_descriptor_before_destroy": _descriptor(process, temp_desc, 16),
    }


def report(label):
    if not hasattr(builtins, "l16_output_descriptor_sink_first"):
        reset()
    print("L16_OUTPUT_DESCRIPTOR_SINK_PROBE_BEGIN", label)
    print("sink_packet", builtins.l16_output_descriptor_sink_first)
    print("L16_OUTPUT_DESCRIPTOR_SINK_PROBE_END", label)
