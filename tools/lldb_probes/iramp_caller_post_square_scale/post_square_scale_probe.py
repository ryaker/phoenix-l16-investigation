import builtins
import struct


def reset():
    builtins.l16_post_square_scale_first = None


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


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}

    base = _u64(data, 0x20)
    first_vec_data = _read(process, base, 16) if base else None
    first_vec4 = _f32s(first_vec_data) if first_vec_data is not None else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": base,
        "qword_28": _u64(data, 0x28),
        "first_vec4": first_vec4,
    }


def _packet(frame, desc_addr, wrapper_addr):
    process = frame.GetThread().GetProcess()
    wrapper_data = _read(process, wrapper_addr, 0x20)
    if wrapper_data is None:
        return {
            "rip": _u(frame, "rip"),
            "rbp": _u(frame, "rbp"),
            "descriptor_addr": desc_addr,
            "wrapper_addr": wrapper_addr,
            "error": "failed to read wrapper/vector",
        }

    source_desc = _u64(wrapper_data, 0)
    scale_vec = _f32s(wrapper_data[0x10:0x20])
    desc = _descriptor(process, desc_addr)
    source_desc_record = _descriptor(process, source_desc) if source_desc else None
    first_vec4 = desc.get("first_vec4") if desc and "error" not in desc else None
    predicted = None
    if first_vec4 is not None:
        predicted = [first_vec4[i] * scale_vec[i] for i in range(4)]

    return {
        "rip": _u(frame, "rip"),
        "rbp": _u(frame, "rbp"),
        "thread_id": frame.GetThread().GetThreadID(),
        "descriptor_addr": desc_addr,
        "wrapper_addr": wrapper_addr,
        "source_desc_from_wrapper": source_desc,
        "source_desc_equals_destination": source_desc == desc_addr,
        "scale_vec_from_wrapper_plus_0x10": scale_vec,
        "descriptor": desc,
        "source_descriptor_record": source_desc_record,
        "predicted_first_vec4_after_scale": predicted,
    }


def hit(frame, bp_loc, internal_dict):
    builtins.l16_post_square_scale_first = _packet(
        frame,
        _u(frame, "rdi"),
        _u(frame, "rsi"),
    )


def report(label):
    if not hasattr(builtins, "l16_post_square_scale_first"):
        reset()
    print("L16_POST_SQUARE_SCALE_PROBE_BEGIN", label)
    print("handoff_packet", builtins.l16_post_square_scale_first)
    print("L16_POST_SQUARE_SCALE_PROBE_END", label)
