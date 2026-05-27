import builtins
import struct


def reset():
    builtins.l16_row_callback_38a30_conversion_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _s32(frame, name):
    return frame.FindRegister(name).GetValueAsSigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _u16s(data):
    return list(struct.unpack("<" + "H" * (len(data) // 2), data))


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _f32_bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _half_bits_from_static_path(value):
    bits = _f32_bits(value)
    sign = (bits ^ (bits & 0x7FFFFFFF)) >> 16
    abs_bits = bits & 0x7FFFFFFF
    if abs_bits < 0x38800000:
        # This mirrors the observed cl=0 subnormal path:
        # abs(value) * 2^24, then truncating float-to-int conversion.
        return sign | int(abs(value) * 16777216.0)
    clamped = min(abs_bits, 0x477FE000)
    return sign | (((clamped + 0xC8000000) & 0xFFFFFFFF) >> 13)


def hit_return(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rsp = _u(frame, "rsp")
    saved = _read(process, rsp + 0x28, 0x18)
    if saved is None:
        builtins.l16_row_callback_38a30_conversion_first = {
            "rip": _u(frame, "rip"),
            "rsp": rsp,
            "error": "failed to read saved callback pointers",
        }
        return

    rounded_down_width = _u64(saved, 0x00)
    source_row = _u64(saved, 0x08)
    dest_row = _u64(saved, 0x10)
    source_bytes = _read(process, source_row, 16) if source_row else None
    dest_bytes = _read(process, dest_row, 12) if dest_row else None

    source_vec4 = _f32s(source_bytes) if source_bytes is not None else None
    dest_words = _u16s(dest_bytes) if dest_bytes is not None else None
    predicted_words = (
        [_half_bits_from_static_path(value) for value in source_vec4[:3]]
        if source_vec4 is not None
        else None
    )

    thread = frame.GetThread()
    caller_pc = thread.GetFrameAtIndex(1).GetPC() if thread.GetNumFrames() > 1 else None
    builtins.l16_row_callback_38a30_conversion_first = {
        "rip": _u(frame, "rip"),
        "caller_pc": caller_pc,
        "thread_id": thread.GetThreadID(),
        "rsp": rsp,
        "rounded_down_width_saved_0x28": rounded_down_width,
        "remaining_width_r12d": _s32(frame, "r12"),
        "source_row_saved_0x30": source_row,
        "dest_row_saved_0x38": dest_row,
        "source_first_vec4": source_vec4,
        "dest_first_12_bytes": list(dest_bytes) if dest_bytes is not None else None,
        "dest_first_6_u16": dest_words[:3] if dest_words is not None else None,
        "predicted_first_3_u16_from_static_path": predicted_words,
        "predicted_matches_dest_first_3": (
            dest_words[:3] == predicted_words
            if dest_words is not None and predicted_words is not None
            else None
        ),
    }


def report(label):
    if not hasattr(builtins, "l16_row_callback_38a30_conversion_first"):
        reset()
    print("L16_ROW_CALLBACK_38A30_CONVERSION_PROBE_BEGIN", label)
    print("conversion_packet", builtins.l16_row_callback_38a30_conversion_first)
    print("L16_ROW_CALLBACK_38A30_CONVERSION_PROBE_END", label)
